#!/usr/bin/env python


# Copyright 2016 - 2018 Sertan Şentürk
#
# This file is part of tomato: https://github.com/sertansenturk/tomato/
#
# tomato is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License v3.0
# along with this program. If not, see http://www.gnu.org/licenses/
#
# If you are using this extractor please cite the following thesis:
#
# Şentürk, S. (2016). Computational analysis of audio recordings and music
# scores for the description and discovery of Ottoman-Turkish makam music.
# PhD thesis, Universitat Pompeu Fabra, Barcelona, Spain.

import json
import logging
from copy import deepcopy

import numpy as np

from ..audio.pitchdistribution import PitchDistribution
from ..converter import Converter
from ..io import IO

logger = logging.Logger(__name__, level=logging.INFO)


class AlignedNoteModel:
    def __init__(self, kernel_width=7.5, step_size=7.5, pitch_threshold=50):
        self.kernel_width = kernel_width
        self.step_size = step_size
        self.pitch_threshold = pitch_threshold  # max threshold for two
        # pitches to be considered close. Used in stable pitch computation

    def get_models(self, pitch, alignednotes, tonic_symbol):
        note_dict = IO.load_music_data('note')

        pitch = np.array(pitch)
        alignednotes_ext = deepcopy(alignednotes)

        note_names = set(an['Symbol'] for an in alignednotes_ext)
        note_models = {}
        for nn in note_names:
            try:
                note_models[nn] = {
                    'notes': [], 'distribution': [], 'stable_pitch': [],
                    'performed_interval': [], 'theoretical_interval': {
                        'Value': (note_dict[nn]['Value'] -
                                  note_dict[tonic_symbol]['Value']),
                        'Unit': 'cent'}, 'theoretical_pitch': []}
            except KeyError:
                logger.warning(
                    u"The note {0:s} is not in the note_dict.".format(nn))

        # compute note trajectories and add to each model
        self._distribute_pitch_trajectories(alignednotes_ext, note_models,
                                            pitch)

        # remove models without any aligned note
        self._remove_unaligned_notes(note_models)

        # update the tonic frequency temporarily
        # NOTE: extremely unlikely but this value might shift to the next bin
        # in the note model computation. Hence we don't assign it to the
        # final tonic value.
        tonic_trajectories = [nn['PitchTrajectory'][:, 1]
                              for nn in note_models[tonic_symbol]['notes']]
        temp_tonic_freq = self._get_stablepitch_distribution(
            tonic_trajectories,
            note_models[tonic_symbol]['theoretical_interval']['Value'])[0]

        # compute the histogram for each model
        self._get_note_histogram(note_models, temp_tonic_freq)

        # update the new tonic frequency
        newtonic = {'alignment': {
            'Value': note_models[tonic_symbol]['stable_pitch']['Value'],
            'Unit': 'Hz', 'Symbol': tonic_symbol, 'Method': 'alignedNoteModel',
            'OctaveWrapped': False, 'Citation': 'SenturkPhDThesis',
            'Procedure': 'Tonic identified from the tonic note model obtained '
                         'from audio-score alignment'}}

        # get the distances wrt tonic
        self._get_tunings(newtonic, note_models)

        # compute the complete histogram without normalization
        recording_distribution = PitchDistribution.from_hz_pitch(
            pitch, ref_freq=temp_tonic_freq, kernel_width=self.kernel_width,
            step_size=self.step_size, norm_type=None)
        recording_distribution.cent_to_hz()

        # normalize all the distributions
        recording_distribution, note_models = self._normalize_distributions(
            recording_distribution, note_models)

        return note_models, recording_distribution, newtonic

    def _get_note_histogram(self, note_models, temp_tonic_freq):
        for nm in note_models.values():
            peak_freq, distribution = self._get_stablepitch_distribution(
                [nn['PitchTrajectory'][:, 1] for nn in nm['notes']],
                nm['theoretical_interval']['Value'],
                ref_freq=temp_tonic_freq)

            nm['stable_pitch'] = {'Value': peak_freq, 'Unit': 'Hz'}
            nm['distribution'] = distribution

    @staticmethod
    def _get_tunings(newtonic, note_models):
        for nm in note_models.values():
            interval = Converter.hz_to_cent(nm['stable_pitch']['Value'],
                                            newtonic['alignment']['Value'])
            nm['performed_interval'] = {'Value': interval, 'Unit': 'cent'}

            theo_pitch = Converter.cent_to_hz(
                nm['theoretical_interval']['Value'],
                newtonic['alignment']['Value'])
            nm['theoretical_pitch'] = {'Value': theo_pitch, 'Unit': 'Hz'}

    @staticmethod
    def _remove_unaligned_notes(note_models):
        for key in note_models.keys():
            if not note_models[key]['notes']:
                note_models.pop(key, None)

    @staticmethod
    def _distribute_pitch_trajectories(alignednotes_ext, note_models, pitch):
        for an in alignednotes_ext:
            if not an['Interval'][0] == an['Interval'][1]:  # not aligned
                trajectory = np.vstack(
                    p for p in pitch
                    if an['Interval'][0] <= p[0] <= an['Interval'][1])
                notetemp = dict(an)
                notetemp['PitchTrajectory'] = trajectory

                try:
                    note_models[an['Symbol']]['notes'].append(notetemp)
                except KeyError:
                    logger.info(u"The note {0:s} is not in the "
                                u"note_dict.".format(an['Symbol']))

    def _get_stablepitch_distribution(self, note_trajectories,
                                      theoretical_interval, ref_freq=None):
        temp_pitch_vals = np.hstack(nn for nn in note_trajectories)

        # useful to keep the bins coinciding with a desired value,
        # e.g. tonic frequency
        if ref_freq is None:
            ref_freq = self._get_median_pitch(temp_pitch_vals)

        distribution = PitchDistribution.from_hz_pitch(
            temp_pitch_vals, ref_freq=ref_freq,
            kernel_width=self.kernel_width, step_size=self.step_size,
            norm_type=None)

        # get the stable pitch as the highest peaks among the peaks close to
        # the theoretical pitch TODO
        peaks = distribution.detect_peaks()
        peak_bins = distribution.bins[peaks[0]]
        peak_vals = distribution.vals[peaks[0]]

        try:
            cand_bool = (abs(peak_bins - theoretical_interval) <
                         self.pitch_threshold)
            stable_pitch_cand = peak_bins[cand_bool]
            cand_occr = peak_vals[cand_bool]

            peak_cent = stable_pitch_cand[np.argmax(cand_occr)]

            # convert to hz scale
            peak_freq = Converter.cent_to_hz(peak_cent, ref_freq)
        except ValueError:  # no stable pitch in the vicinity, probably a
            # misalignment
            peak_freq = None

        # convert to hz scale
        distribution.cent_to_hz()

        return peak_freq, distribution

    @staticmethod
    def _get_median_pitch(pitch):
        if pitch.ndim > 1:
            pitch = pitch[:, 1]

        # filter the nan, inf and inaudible
        pitch = pitch[~np.isnan(pitch)]
        pitch = pitch[~np.isinf(pitch)]
        pitch = pitch[pitch >= 20.0]

        return np.median(pitch)

    @staticmethod
    def _normalize_distributions(recording_distribution, note_models):
        dist_norm = deepcopy(recording_distribution)

        # sum normalization on the audio recording
        dist_norm.normalize(norm_type='sum')

        # compute the normalization factor
        ini_max_val = max(recording_distribution.vals)
        fin_max_val = max(dist_norm.vals)
        norm_factor = fin_max_val / ini_max_val

        for nm in note_models.values():
            nm['distribution'].vals *= norm_factor

        return dist_norm, note_models

    @staticmethod
    def to_json(note_models, json_path=None):
        # conversions for json serialization
        note_models_ser = deepcopy(note_models)
        for nm in note_models_ser.values():
            # convert the distribution object to dict
            nm['distribution'] = nm['distribution'].to_dict()

            # convert the pitchtrajectories to lists from numpy arrays
            for nn in nm['notes']:
                nn['PitchTrajectory'] = nn['PitchTrajectory'].tolist()

        if json_path is None:
            return json.dumps(note_models_ser, indent=4)
        else:
            json.dump(note_models_ser, open(json_path, 'w'), indent=4)

    @staticmethod
    def plot(note_models, pitch_distribution, alignednotes, pitch):
        import matplotlib.pyplot as plt

        pitch = np.array(pitch)

        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.plot(pitch[:, 0], pitch[:, 1], 'g', label='Pitch', alpha=0.7)
        fig.subplots_adjust(wspace=0)
        ax1.set_xlabel('Time (sec)')
        ax1.yaxis.grid(True)

        for note in alignednotes:
            ax1.plot(note['Interval'],
                     [note['PerformedPitch']['Value'],
                      note['PerformedPitch']['Value']],
                     'r', alpha=0.4, linewidth=4)

        ax2.plot(pitch_distribution.vals, pitch_distribution.bins, '-.',
                 color='#000000', alpha=0.9)
        for key in note_models.keys():
            ax2.plot(note_models[key]['distribution'].vals,
                     note_models[key]['distribution'].bins, label=key)

        ax2.set_yticks(
            [nm['stable_pitch']['Value'] for nm in note_models.values()])
        ax2.set_yticklabels(
            [key + ', ' + "%.1f" % val['stable_pitch']['Value'] +
             ' Hz, ' + "%.1f" % val['performed_interval']['Value'] + ' cents'
             for key, val in note_models.items()])
        ax2.axis('off')
        ax2.set_ylim([np.min(pitch_distribution.bins),
                      np.max(pitch_distribution.bins)])
        ax2.yaxis.grid(True)

        ax2.set_xticklabels([])
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)

        return fig, (ax1, ax2)
