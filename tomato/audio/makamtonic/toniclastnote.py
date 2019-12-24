
# Copyright 2015 - 2018 Hasan Sercan Atlı & Sertan Şentürk
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
# If you are using this extractor please cite the following paper:
#
# Atlı, H. S., Bozkurt, B., and Şentürk, S. (2015). A method for tonic
# frequency identification of Turkish makam music recordings. In Proceedings
# of 5th International Workshop on Folk Music Analysis (FMA 2015),
# pages 119–122, Paris, France.

from copy import deepcopy

import numpy as np

from ..pitchdistribution import PitchDistribution
from ..pitchfilter import PitchFilter
from ...converter import Converter


class TonicLastNote:
    def __init__(self, stable_pitch_dev=25, kernel_width=7.5, step_size=7.5,
                 min_freq=64, max_freq=1024, lower_interval_thres=0.965,
                 upper_interval_thres=1.035, min_chunk_size=60):
        self.stable_pitch_dev = stable_pitch_dev  # cents, the max difference
        # between two pitches to be considered the same. Used in tonic
        # octave correction, 25 cents
        self.kernel_width = kernel_width  # cents, kernel width of the pitch
        # distribution, 7-5 cents ~1/3 Holderian comma
        self.step_size = step_size  # cents, step size of the bins of the pitch
        # distribution, 7-5 cents ~1/3 Holderian comma

        self.min_freq = min_freq  # minimum frequency allowed
        self.max_freq = max_freq  # maximum frequency allowed
        self.lower_interval_thres = lower_interval_thres  # the smallest value
        # the interval can stay before a new chunk is formed
        self.upper_interval_thres = upper_interval_thres  # the highest value
        # the interval can stay before a new chunk is formed
        self.min_chunk_size = min_chunk_size  # minimum number of samples to
        # form a chunk

    @staticmethod
    def find_nearest(array, value):
        distance = [abs(element - value) for element in array]
        idx = distance.index(min(distance))
        return array[idx]

    def identify(self, pitch, plot=False):
        """
        Identify the tonic by detecting the last note and extracting the
        frequency
        """
        pitch_sliced = np.array(deepcopy(pitch))

        # trim silence in the end
        sil_trim_len = len(np.trim_zeros(pitch_sliced[:, 1], 'b'))  # remove
        pitch_sliced = pitch_sliced[:sil_trim_len, :]  # trailing zeros

        # slice the pitch track to only include the last 10% of the track
        # for performance reasons
        pitch_len = pitch_sliced.shape[0]
        pitch_sliced = pitch_sliced[-int(pitch_len * 0.1):, :]

        # compute the pitch distribution and distribution peaks
        dummy_freq = 440.0
        distribution = PitchDistribution.from_hz_pitch(
            np.array(pitch)[:, 1], ref_freq=dummy_freq,
            kernel_width=self.kernel_width, step_size=self.step_size)

        # get pitch chunks
        flt = PitchFilter(lower_interval_thres=self.lower_interval_thres,
                          upper_interval_thres=self.upper_interval_thres,
                          min_freq=self.min_freq, max_freq=self.max_freq)
        pitch_chunks = flt.decompose_into_chunks(pitch_sliced)

        pitch_chunks = flt.post_filter_chunks(pitch_chunks)

        tonic = {"value": None, "unit": "Hz",
                 "timeInterval": {"value": None, "unit": 'sec'},
                 "octaveWrapped": False,  # octave correction is done
                 "procedure": "Tonic identification by last note detection",
                 "citation": 'Atlı, H. S., Bozkurt, B., Şentürk, S. (2015). '
                             'A Method for Tonic Frequency Identification of '
                             'Turkish Makam Music Recordings. In Proceedings '
                             'of 5th International Workshop on Folk Music '
                             'Analysis, pages 119–122, Paris, France.'}

        # try all chunks starting from the last as the tonic candidate,
        # considering the octaves
        for chunk in reversed(pitch_chunks):
            last_note = np.median(chunk[:, 1])

            # check all the pitch classes of the last note as a tonic candidate
            # by checking the vicinity in the stable pitches
            tonic_candidate = self.check_tonic_w_octave_cor(
                last_note, deepcopy(distribution))

            # assign the tonic if there is an estimation
            if tonic_candidate is not None:
                tonic['value'] = tonic_candidate
                tonic['timeInterval']['value'] = [chunk[0, 0], chunk[-1, 0]]

                # convert distribution bins to frequency
                distribution.cent_to_hz()
                break

        if plot:
            self.plot(pitch_sliced, tonic, pitch_chunks, distribution)

        return tonic, pitch_sliced, pitch_chunks, distribution

    def check_tonic_w_octave_cor(self, tonic, distribution):
        # shift the distribution to tonic
        distribution.bins -= Converter.hz_to_cent(tonic, distribution.ref_freq)
        distribution.ref_freq = tonic

        # get the stable pitches
        peaks = distribution.detect_peaks()
        peak_idx = peaks[0]
        stable_pitches = distribution.bins[peak_idx]

        # find all the frequencies in the tonic candidate's pitch class
        pitches_in_tonic_pitch_class = [
            sp for sp in stable_pitches
            if min([sp % 1200, 1200 - (sp % 1200)]) < self.stable_pitch_dev]

        # sum all the pitch occurrences in the pitch distribution starting from
        # these pitches till their octave
        pitch_weights = []
        for pp in pitches_in_tonic_pitch_class:
            vals_in_octave = distribution.vals[(pp <= distribution.bins) *
                                               (distribution.bins < pp + 1200)]
            pitch_weights.append(np.sum(vals_in_octave))

        # the candidate which accumulates the highest weight is the tonic
        try:
            tonic_corr_cent = pitches_in_tonic_pitch_class[
                pitch_weights.index(max(pitch_weights))]

            return Converter.cent_to_hz(tonic_corr_cent, tonic)
        except ValueError:
            return None  # no stable pitch class found for the given frequency

    @staticmethod
    def plot(pitch, tonic, pitch_chunks, distribution):
        import matplotlib.pyplot as plt
        import matplotlib.ticker

        _, (ax1, ax2, ax3) = plt.subplots(3, num=None, figsize=(18, 8), dpi=80)
        plt.subplots_adjust(left=None, bottom=None, right=None, top=None,
                            wspace=0, hspace=0.4)

        # plot title
        ax1.set_title('Pitch Distribution')
        ax1.set_xlabel('Frequency (Hz)')
        ax1.set_ylabel('Frequency of occurrence')

        # log scaling the x axis
        ax1.set_xscale('log', basex=2, nonposx='clip')
        ax1.xaxis.set_major_formatter(
            matplotlib.ticker.FormatStrFormatter('%d'))

        # recording distribution
        ax1.plot(distribution.bins, distribution.vals, label='SongHist',
                 ls='-', c='b', lw='1.5')

        # peaks
        peaks = distribution.detect_peaks()
        ax1.plot(distribution.bins[peaks[0]], peaks[1], 'cD', ms=6, c='r')

        # tonic
        ax1.plot(tonic['value'],
                 distribution.vals[np.where(
                     distribution.bins == tonic['value'])[0]], 'cD', ms=10)

        # pitch distributiongram
        ax2.plot([element[0] for element in pitch],
                 [element[1] for element in pitch], ls='-', c='r', lw='0.8')
        ax2.vlines([element[0][0] for element in pitch_chunks], 0,
                   max([element[1]] for element in pitch))
        ax2.set_xlabel('Time (secs)')
        ax2.set_ylabel('Frequency (Hz)')

        ax3.plot([element[0] for element in pitch_chunks[-1]],
                 [element[1] for element in pitch_chunks[-1]])
        ax3.set_title("Last Chunk")
        ax3.set_xlabel('Time (secs)')
        ax3.set_ylabel('Frequency (Hz)')
        plt.show()
