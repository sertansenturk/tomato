#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 - 2018 Sertan Şentürk
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

import numpy as np
import copy
import matplotlib.pyplot as plt


class AlignedPitchFilter(object):
    def __init__(self):
        self.max_boundary_tol = 3  # seconds

    def filter(self, pitch, notes):
        # IMPORTANT: In the audio-score alignment step, the pitch value
        # of each note is computed from the theoretical pitch distance
        # from the tonic and de-normalized according to the tonic
        # frequency of the performance. The value is not computed from
        # THE PITCH TRAJECTORY OF THE NOTE; it is just the THEORETICAL
        # FREQUENCY OF THE NOTE SYMBOL ACCORDING TO THE TONIC FREQUENCY
        # The performed stable pitch of the note will be computed in the
        # aligned-note-models
        pitch_corrected = np.copy(pitch)
        notes_corrected = copy.deepcopy(notes)

        notes_corrected = self._remove_rests_and_skipped_notes(notes_corrected)

        # group the notes into sections
        synth_pitch = self._notes_to_synth_pitch(
            notes_corrected, pitch_corrected[:, 0])

        # octave correction
        for i, sp in enumerate(synth_pitch[:, 1]):
            pitch_corrected[i][1] = self._move_to_closest_octave(
                pitch_corrected[i][1], sp)

        self._get_pitch_trajectories(notes_corrected, pitch_corrected)

        return pitch_corrected, notes_corrected, synth_pitch.tolist()

    @staticmethod
    def _remove_rests_and_skipped_notes(notes_corrected):
        # remove skipped notes
        notes_corrected = ([n for n in notes_corrected
                            if not n['Interval'][0] == n['Interval'][1]])
        # remove rests
        notes_corrected = [n for n in notes_corrected if
                           n['TheoreticalPitch']['Value']]
        return notes_corrected

    @staticmethod
    def _get_pitch_trajectories(notes_corrected, pitch_corrected):
        for nc in notes_corrected:
            trajectory = np.vstack(
                p[1] for p in pitch_corrected
                if nc['Interval'][0] <= p[0] <= nc['Interval'][1])
            nc['PerformedPitch']['Value'] = np.median(trajectory).tolist()

    def _notes_to_synth_pitch(self, notes, time_stamps):
        synth_pitch = np.array([0] * len(time_stamps))

        for i in range(0, len(notes)):
            prevlabel = ([] if i == 0 else
                         notes[i - 1]['Label'].split('--')[0])
            label = notes[i]['Label'].split('--')[0]
            nextlabel = ([] if i == len(notes) - 1 else
                         notes[i + 1]['Label'].split('--')[0])

            # let the synthetic pitch continue in the boundaries a little bit
            # more
            startidx = self._preinterpolate_synth(
                i, label, notes, prevlabel, time_stamps)
            self._postinterpolate_synth(i, label, nextlabel, notes, startidx,
                                        synth_pitch, time_stamps)

        # add time_stamps
        synth_pitch = np.transpose(np.vstack((time_stamps, synth_pitch)))

        return synth_pitch

    def _postinterpolate_synth(self, i, label, next_label, notes, start_idx,
                               synth_pitch, time_stamps):

        if not next_label:
            # post interpolation end time on the last note
            endidx = self._find_closest_sample_idx(
                notes[i]['Interval'][1] + self.max_boundary_tol,
                time_stamps)
        elif not label == next_label:
            # post interpolation end time on a group end
            nextstartidx = self._find_closest_sample_idx(
                notes[i + 1]['Interval'][0], time_stamps)
            endidx = self._find_closest_sample_idx(
                notes[i]['Interval'][1] + self.max_boundary_tol,
                time_stamps[:nextstartidx])
        else:
            # post interpolation within a group
            nextstartidx = self._find_closest_sample_idx(
                notes[i + 1]['Interval'][0], time_stamps)
            endidx = nextstartidx - 1
        synth_pitch[start_idx:endidx + 1] = \
            notes[i]['TheoreticalPitch']['Value']

    def _preinterpolate_synth(self, i, label, notes, prevlabel, time_stamps):
        # pre interpolation start time on the first note
        if not prevlabel:
            startidx = self._find_closest_sample_idx(
                notes[i]['Interval'][0] - self.max_boundary_tol,
                time_stamps)
        elif not label == prevlabel:
            # post interpolation start time on a group start

            # recalculate the end time of the previous
            tempstartidx = self._find_closest_sample_idx(
                notes[i]['Interval'][0], time_stamps)
            prevendidx = self._find_closest_sample_idx(
                notes[i - 1]['Interval'][1] + self.max_boundary_tol,
                time_stamps[:tempstartidx])

            startidx = prevendidx + self._find_closest_sample_idx(
                notes[i]['Interval'][0] - self.max_boundary_tol,
                time_stamps[prevendidx:]) + 1
        else:  # no pre interpolation
            startidx = self._find_closest_sample_idx(
                notes[i]['Interval'][0], time_stamps)
        return startidx

    @staticmethod
    def _find_closest_sample_idx(val, sample_vals):
        return np.argmin(abs(sample_vals - val))

    @classmethod
    def _move_to_closest_octave(cls, pp, sp):
        minpp = pp
        if not (pp in [0, np.nan] or sp in [0, np.nan]):
            cent_diff = cls._hz2cent(pp, sp)
            octave_cands = [cent_diff, cent_diff - 1200]
            cand_dist = [abs(oc) for oc in octave_cands]
            closest_cent_diff = octave_cands[cand_dist.index(min(cand_dist))]

            minpp = cls._cent2hz(closest_cent_diff, sp)

        return minpp

    @staticmethod
    def _cent2hz(cent_val, ref_hz):
        try:
            return ref_hz * 2 ** (cent_val / 1200.0)
        except TypeError:  # _NaN_; rest
            return None

    @staticmethod
    def _hz2cent(val, ref_hz):
        return 1200.0 * np.log2(val / ref_hz)

    @staticmethod
    def _decompose_into_chunks(pitch, bottom_limit=0.7, upper_limit=1.3):
        pitch_chunks = []
        temp_pitch = np.array([])
        # starts at the first sample
        for i in range(1, len(pitch) - 1):
            # ignore chunks with 0 frequency values
            if pitch[i][1] == 0:
                pass
            # non-zero chunks
            else:
                interval = float(pitch[i + 1][1]) / float(pitch[i][1])
                temp_pitch = (np.vstack((temp_pitch, pitch[i]))
                              if temp_pitch.size > 0 else pitch[i])

                if not bottom_limit < interval < upper_limit:
                    if temp_pitch:
                        pitch_chunks.append(temp_pitch)
                    temp_pitch = np.array([])
        if temp_pitch:
            pitch_chunks.append(temp_pitch)

        return pitch_chunks

    @staticmethod
    def plot(pitch, pitch_corrected, notes_corrected):
        # remove zeros for plotting
        pitch_plot = np.copy(pitch)
        pitch_plot[pitch_plot[:, 1] == 0, 1] = np.NAN

        pitch_corrected_plot = np.copy(pitch_corrected)
        pitch_corrected_plot[pitch_corrected_plot[:, 1] == 0, 1] = np.NAN

        fig, ax = plt.subplots()

        # plot pitch tracks
        ax.plot(pitch_plot[:, 0], pitch_plot[:, 1], 'g', label='Pitch',
                linewidth=3, alpha=0.7)
        ax.plot(pitch_corrected_plot[:, 0], pitch_corrected_plot[:, 1], 'b',
                linewidth=1, label=u'Corrected Pitch')

        plt.xlabel('Time (sec)')
        plt.ylabel('Frequency (Hz)')

        plt.grid(True)

        # plot notes except the last one
        for note in notes_corrected[:-1]:
            ax.plot(note['Interval'], [note['PerformedPitch']['Value'],
                                       note['PerformedPitch']['Value']],
                    'r', alpha=0.4, linewidth=6)

        # plot last note for labeling
        dmy_note = notes_corrected[-1]
        ax.plot(dmy_note['Interval'], [dmy_note['PerformedPitch']['Value'],
                                       dmy_note['PerformedPitch']['Value']],
                'r', label=u'Aligned Notes', alpha=0.4, linewidth=6)

        # set y axis limits
        pitch_vals = np.hstack((pitch_plot[:, 1], pitch_corrected_plot[:, 1]))
        pitch_vals = pitch_vals[~np.isnan(pitch_vals)]

        min_y = np.min(pitch_vals)
        max_y = np.max(pitch_vals)
        range_y = max_y - min_y

        ax.set_ylim([min_y - range_y * 0.1, max_y + range_y * 0.1])

        # set x axis limits
        time_vals = np.hstack((pitch_plot[:, 0], pitch_corrected_plot[:, 0]))

        min_x = np.min(time_vals)
        max_x = np.max(time_vals)

        ax.set_xlim([min_x, max_x])

        # place legend
        ax.legend(loc='upper right')
