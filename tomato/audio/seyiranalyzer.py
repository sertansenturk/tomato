#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 Sertan Şentürk
#
# This file is part of tomato: https://github.com/sertansenturk/tomato/
#
# tomato is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation (FSF), either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License v3.0
# along with this program. If not, see http://www.gnu.org/licenses/
#
# If you are using this extractor please cite the following thesis:
#
# Şentürk, S. (2016). Computational Analysis of Audio Recordings and Music
# Scores for the Description and Discovery of Ottoman-Turkish Makam Music.
# Ph.D. thesis, Universitat Pompeu Fabra, Barcelona, Spain.


import numpy as np
import matplotlib.pyplot as plt
from morty.pitchdistribution import PitchDistribution
from morty.converter import Converter
import json
import copy


class SeyirAnalyzer(object):
    _dummy_ref_freq = 440.0  # hz
    citation = u"B. Bozkurt, Computational analysis of overall melodic " \
               u"progression for Turkish Makam Music, in Penser " \
               u"l’improvisation edited by Mondher Ayari, pp. 289-298, " \
               u"ISBN: 9782752102485, 2015, Delatour France, Sampzon."

    def __init__(self, kernel_width=7.5, step_size=7.5):
        self.kernel_width = kernel_width
        self.step_size = step_size

    def _get_settings(self):
        return {'kernel_width': self.kernel_width, 'step_size': self.step_size,
                'citation': self.citation}

    def analyze(self, pitch, frame_dur=20.0, hop_ratio=0.5):
        hop_size = frame_dur * hop_ratio

        pitch = np.array(pitch)
        tt = pitch[:, 0]
        pp = pitch[:, 1]

        # start the first frame "centered" around 0 seconds
        tb = -frame_dur / 2.0
        t_intervals = []
        t_center = []
        while tb < tt[-1]:
            # make sure the frame boundaries do not exceed the audio time
            t_intervals.append([max([0.0, tb]), min([tb + frame_dur, tt[-1]])])
            t_center.append(min([max([tb + frame_dur / 2.0, 0]), tt[-1]]))
            tb += hop_size

        return self._compute_seyir_features_per_interval(pp, tt, t_intervals,
                                                         t_center)

    def _compute_seyir_features_per_interval(self, pp, tt, t_intervals,
                                             t_center):
        seyir_features = []
        maxdur = max(ti[1] - ti[0] for ti in t_intervals)

        for ti, tc in zip(t_intervals, t_center):
            p_cent, p_sliced = self._slice_pitch(pp, ti, tt)

            if p_cent.size == 0:  # silence
                seyir_features.append(
                    {'pitch_distribution': [], 'average_pitch': np.nan,
                     'stable_pitches': [], 'time_interval': ti,
                     'time_center': tc})
            else:
                pd = PitchDistribution.from_cent_pitch(
                    p_cent, ref_freq=self._dummy_ref_freq,
                    kernel_width=self.kernel_width, step_size=self.step_size)

                # reconvert to Hz
                pd.cent_to_hz()

                # normalize to 1 (instead of the area under the curve)
                maxval = max(pd.vals)
                num_ratio = float(len(p_cent)) / len(p_sliced)  # ratio of
                # number of samples
                time_ratio = (ti[1] - ti[0]) / maxdur
                pd.vals = pd.vals * num_ratio * time_ratio / maxval

                # get the stable pitches, i.e. peaks
                peak_idx, peak_vals = pd.detect_peaks()
                stable_pitches = [{'frequency': float(pd.bins[idx]),
                                   'value': float(val)}
                                  for idx, val in zip(peak_idx, peak_vals)]

                # get the average pitch
                avpitch = Converter.cent_to_hz(np.mean(p_cent),
                                               self._dummy_ref_freq)

                seyir_features.append(
                    {'pitch_distribution': pd, 'average_pitch': avpitch,
                     'stable_pitches': stable_pitches, 'time_interval': ti,
                     'time_center': tc})

        return seyir_features

    def _slice_pitch(self, pp, ti, tt):
        p_sliced = [p for t, p in zip(tt, pp) if ti[1] > t >= ti[0]]
        p_cent = Converter.hz_to_cent(
            p_sliced, self._dummy_ref_freq, min_freq=20.0)

        # pop nan and inf
        p_cent = p_cent[~np.isnan(p_cent)]
        p_cent = p_cent[~np.isinf(p_cent)]  # shouldn't exist, but anyways...
        return p_cent, p_sliced

    @staticmethod
    def to_json(seyir_features, json_out=None):
        seyir_copy = copy.deepcopy(seyir_features)
        SeyirAnalyzer.serialize(seyir_copy)

        if json_out is None:
            return json.dumps(seyir_copy)
        else:
            json.dump(seyir_copy, open(json_out, 'w'))

    @staticmethod
    def from_json(json_in):
        try:
            seyir_features = json.load(open(json_in))
        except IOError:
            seyir_features = json.loads(json_in)

        SeyirAnalyzer.deserialize(seyir_features)

        return seyir_features

    @staticmethod
    def serialize(seyir_features):
        for sf in seyir_features:
            try:  # convert pitch distribution objects to dicts
                sf['pitch_distribution'] = sf[
                    'pitch_distribution'].to_dict()
            except AttributeError:  # empty pitch distribution
                assert not sf['pitch_distribution'], \
                    'non-empty, non-object pitch distribution encountered'

    @staticmethod
    def deserialize(seyir_features):
        for sf in seyir_features:
            try:
                sf['pitch_distribution'] = PitchDistribution.from_dict(
                    sf['pitch_distribution'])
            except AttributeError:  # empty pitch distribution
                assert not sf['pitch_distribution'], \
                    'non-empty, non-object pitch distribution encountered'

    @staticmethod
    def plot(seyir_features, ax=None, plot_average_pitch=True,
             plot_stable_pitches=True, plot_distribution=False):

        if ax is None:
            fig, ax = plt.subplots()

        if plot_distribution:
            SeyirAnalyzer._pitch_distrib_plotter(ax, seyir_features)

        if plot_stable_pitches:
            SeyirAnalyzer._stable_pitch_plotter(ax, seyir_features)

        if plot_average_pitch:
            SeyirAnalyzer._average_pitch_plotter(ax, seyir_features)

        ax.set_xlim([seyir_features[0]['time_interval'][0],
                     seyir_features[-1]['time_interval'][1]])
        ax.set_xlabel('Time (sec)')
        ax.set_ylabel('Frequency (Hz)')

    @staticmethod
    def _average_pitch_plotter(ax, seyir_features):
        tt = [sf['time_center'] for sf in seyir_features]
        pp = [sf['average_pitch'] for sf in seyir_features]
        ax.plot(tt, pp, color='k', linewidth=3)

    @staticmethod
    def _stable_pitch_plotter(ax, seyir_features):
        num_frames = len(seyir_features)
        for sf in seyir_features:
            if sf['stable_pitches']:  # ignore silent frame
                t_center = sf['time_center']
                max_peak = max([sp['value']
                                for sp in sf['stable_pitches']])
                for sp in sf['stable_pitches']:
                    clr = 'r' if sp['value'] == max_peak else 'b'
                    # map the values from 0-1 to 1-6
                    marker_thickness = ((sp['value'] * 5 + 1) * 100 /
                                        num_frames)
                    ax.plot(t_center, sp['frequency'], 'o',
                            color=clr, ms=marker_thickness)

    @staticmethod
    def _pitch_distrib_plotter(ax, seyir_features):
        time_centers = [sf['time_center'][0] for sf in seyir_features]
        min_time = min(np.diff(time_centers))
        for sf in seyir_features:
            if sf['pitch_distribution']:  # ignore silent frame
                # plot the distributions through time
                yy = sf['pitch_distribution'].bins
                tt = (sf['time_center'] +
                      sf['pitch_distribution'].vals * min_time * 2)
                ax.plot(tt, yy)
