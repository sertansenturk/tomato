# Copyright 2014 - 2018 Hasan Sercan Atlı & Sertan Şentürk
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
# The algorithm is based on the pitch filter method originally explained in:
#
# Bozkurt, B. An Automatic Pitch Analysis Method for Turkish Maqam Music.
# Journal of New Music Research. 37(1), 1-13.
#
# If you are using this implementation, please cite the following paper:
#
# Atlı, H. S., Uyar, B., Şentürk, S., Bozkurt, B., and Serra, X. (2014).
# Audio feature extraction for exploring Turkish makam music. In Proceedings
# of 3rd International Conference on Audio Technologies for Music and Media
# (ATMM 2014), pages 142–153, Ankara, Turkey.

import numpy as np


class PitchFilter:
    def __init__(self, lower_interval_thres=0.7, upper_interval_thres=1.3,
                 min_chunk_size=40, min_freq=64, max_freq=1024):

        # the smallest value the interval can stay before a new chunk is formed
        self.lower_interval_thres = lower_interval_thres
        # the highest value the interval can stay before a new chunk is formed
        self.upper_interval_thres = upper_interval_thres
        # minimum number of samples to form a chunk
        self.min_chunk_size = min_chunk_size
        self.min_freq = min_freq  # minimum frequency allowed
        self.max_freq = max_freq  # maximum frequency allowed

    def post_filter_chunks(self, pitch_chunks):
        """
        Postfilter for the pitchChunks
        deletes the zero chunks
        deletes the chunks smaller than 50 samples(default)
        """
        # deleting Zero chunks
        zero_chunks = [i for i in range(0, len(pitch_chunks))
                       if pitch_chunks[i][0][1] == 0]
        if zero_chunks:
            pitch_chunks = np.delete(pitch_chunks, zero_chunks)

        # deleting small Chunks
        small_chunks = [i for i in range(0, len(pitch_chunks))
                        if len(pitch_chunks[i]) <= self.min_chunk_size]
        if small_chunks:
            pitch_chunks = np.delete(pitch_chunks, small_chunks)

        # frequency limit
        limit_chunks = [i for i in range(0, len(pitch_chunks))
                        if pitch_chunks[i][0][1] >= self.max_freq or
                        pitch_chunks[i][0][1] <= self.min_freq]
        if limit_chunks:
            pitch_chunks = np.delete(pitch_chunks, limit_chunks)

        return pitch_chunks

    def decompose_into_chunks(self, pitch):
        """
        decomposes the given pitch track into the chunks.
        """
        pitch_chunks = []
        temp_pitch = []

        # starts at the first sample
        for i in range(0, len(pitch) - 1):
            # separation of the zero chunks
            if pitch[i][1] == 0:
                if pitch[i + 1][1] == 0:
                    temp_pitch.append(pitch[i])
                    if i + 1 == len(pitch) - 1:  # last element
                        temp_pitch.append(pitch[i + 1])
                else:
                    temp_pitch.append(pitch[i])
                    if len(temp_pitch) > 0:
                        pitch_chunks.append(np.array(temp_pitch))
                    if i + 1 == len(pitch) - 1:  # last element
                        temp_pitch = [pitch[i + 1]]
                    else:
                        temp_pitch = []
            # non-zero chunks
            else:
                interval = float(pitch[i + 1][1]) / float(pitch[i][1])
                if (self.lower_interval_thres < interval <
                        self.upper_interval_thres):
                    temp_pitch.append(pitch[i])
                    if i + 1 == len(pitch) - 1:  # last element
                        temp_pitch.append(pitch[i + 1])
                else:
                    temp_pitch.append(pitch[i])
                    if len(temp_pitch) > 0:
                        pitch_chunks.append(np.array(temp_pitch))
                    if i + 1 == len(pitch) - 1:  # last element
                        temp_pitch = [pitch[i + 1]]
                    else:
                        temp_pitch = []
        if len(temp_pitch) > 0:
            pitch_chunks.append(np.array(temp_pitch))

        return pitch_chunks

    @staticmethod
    def recompose_chunks(pitch_chunks):
        """
        recomposes the given pitch chunks as a new pitch track
        """
        pitch = [pitch_chunks[i][j] for i in range(len(pitch_chunks))
                 for j in range(len(pitch_chunks[i]))]
        return np.array(pitch)

    @staticmethod
    def are_close(num1, num2):
        d = abs(num1 - num2)
        av = (num1 + num2) / 2

        if av == 0:
            return True
        if (d / av) < 0.2:
            return True
        return False

    def correct_octave_errors_by_chunks(self, pitch):
        pitch_chunks = self.decompose_into_chunks(pitch=pitch)

        zero_chunks = []
        zero_ind = []
        for j, p_chk in enumerate(pitch_chunks):
            if float(p_chk[0][1]) == 0.:
                zero_chunks.append([j, p_chk])
                zero_ind.append(j)
        pitch_chunks = list(np.delete(pitch_chunks, zero_ind))

        for i in range(1, len(pitch_chunks) - 1):
            if (len(pitch_chunks[i]) <= len(pitch_chunks[i - 1]) * 1.2) or \
                    (len(pitch_chunks[i]) <= len(pitch_chunks[i + 1]) * 1.2):

                med_chunk_i = np.median([element[1]
                                         for element in pitch_chunks[i]])
                med_chunk_follow = np.median(
                    [element[1] for element in pitch_chunks[i + 1]])
                med_chunk_prev = np.median(
                    [element[1] for element in pitch_chunks[i - 1]])

                if ((self.are_close(pitch_chunks[i][0][1] / 2.,
                                    pitch_chunks[i - 1][-1][1]) and
                     (pitch_chunks[i][-1][1] / 1.5 >
                      pitch_chunks[i + 1][0][1])) or
                    (self.are_close(med_chunk_i / 2., med_chunk_prev) and
                     med_chunk_i / 1.5 > med_chunk_follow)):
                    for j in range(0, len(pitch_chunks[i])):
                        pitch_chunks[i][j][1] /= 2.

                elif (self.are_close(pitch_chunks[i][-1][1] / 2.,
                                     pitch_chunks[i + 1][0][1]) and
                      (pitch_chunks[i][0][1] / 1.5 >
                       pitch_chunks[i - 1][-1][1])) or \
                     (self.are_close(med_chunk_i / 2., med_chunk_follow) and
                      med_chunk_i / 1.5 > med_chunk_prev):
                    for j in range(0, len(pitch_chunks[i])):
                        pitch_chunks[i][j][1] /= 2.

                # other condition
                elif (self.are_close(pitch_chunks[i][0][1] * 2.,
                                     pitch_chunks[i - 1][-1][1]) and
                      (pitch_chunks[i][-1][1] * 1.5 <
                       pitch_chunks[i + 1][0][1])) or \
                     (self.are_close(med_chunk_i * 2., med_chunk_prev) and
                      med_chunk_prev * 1.5 < med_chunk_follow):
                    for j in range(0, len(pitch_chunks[i])):
                        pitch_chunks[i][j][1] *= 2.

                elif ((pitch_chunks[i][0][1] * 1.5 <
                       pitch_chunks[i - 1][-1][1] and
                       self.are_close(pitch_chunks[i][-1][1] * 2.,
                                      pitch_chunks[i + 1][0][1])) or
                      (self.are_close(med_chunk_prev * 2, med_chunk_follow)
                       and med_chunk_i * 1.5 < med_chunk_prev)):
                    for j in range(0, len(pitch_chunks[i])):
                        pitch_chunks[i][j][1] *= 2.

        for z_chk in zero_chunks:
            pitch_chunks.insert(z_chk[0], z_chk[1])
        pitch = self.recompose_chunks(pitch_chunks=pitch_chunks)
        return pitch

    def correct_jumps(self, pitch):
        for i in range(4, len(pitch) - 6):
            if self.are_close(pitch[i - 4][1], pitch[i - 3][1]) and \
                    self.are_close(pitch[i - 3][1], pitch[i - 2][1]) and \
                    self.are_close(pitch[i - 2][1], pitch[i - 1][1]):

                # quadruple point
                if self.are_close(pitch[i + 4][1], pitch[i + 5][1]) and \
                        self.are_close(pitch[i + 5][1], pitch[i + 6][1]):
                    if not self.are_close(pitch[i][1], pitch[i - 1][1]) and \
                            not self.are_close(pitch[i][1], pitch[i + 4][1]):
                        pitch[i][1] = pitch[i - 1][1]
                    if not self.are_close(pitch[i + 3][1], pitch[i - 1][1]) \
                            and not self.are_close(pitch[i + 3][1],
                                                   pitch[i + 4][1]):
                        pitch[i + 3][1] = pitch[i + 4][1]

                # triple point
                if self.are_close(pitch[i + 3][1], pitch[i + 4][1]) \
                        and self.are_close(pitch[i + 4][1], pitch[i + 5][1]):
                    if not self.are_close(pitch[i][1], pitch[i - 1][1]) \
                            and not self.are_close(pitch[i][1],
                                                   pitch[i + 3][1]):
                        pitch[i][1] = pitch[i - 1][1]
                    if not self.are_close(pitch[i + 2][1], pitch[i - 1][1])\
                            and not self.are_close(pitch[i + 2][1],
                                                   pitch[i + 3][1]):
                        pitch[i + 2][1] = pitch[i + 3][1]

                # double point
                if self.are_close(pitch[i + 2][1], pitch[i + 3][1]) and \
                        self.are_close(pitch[i + 3][1], pitch[i + 4][1]):
                    if not self.are_close(pitch[i][1], pitch[i - 1][1]) and \
                            not self.are_close(pitch[i][1], pitch[i + 2][1]):
                        pitch[i][1] = pitch[i - 1][1]

                    if not self.are_close(pitch[i + 1][1], pitch[i - 1][1]) \
                            and not self.are_close(pitch[i + 1][1],
                                                   pitch[i + 2][1]):
                        pitch[i + 1][1] = pitch[i + 2][1]

                # single point
                if self.are_close(pitch[i + 1][1], pitch[i + 2][1]) and \
                        self.are_close(pitch[i + 2][1], pitch[i + 3][1]):
                    if not self.are_close(pitch[i][1], pitch[i - 1][1]) and \
                            not self.are_close(pitch[i][1], pitch[i + 1][1]):
                        pitch[i][1] = pitch[i - 1][1]
        return pitch

    def correct_oct_error(self, pitch):
        pitch_series = [pitch[i][1] for i in range(len(pitch))]
        midf0 = (np.median(pitch_series) + np.mean(pitch_series)) / 2

        for i in range(4, len(pitch) - 2):
            # if previous values are continuous
            if self.are_close(pitch[i - 1][1], pitch[i - 2][1]) and \
                    self.are_close(pitch[i - 2][1], pitch[i - 3][1]) and \
                    self.are_close(pitch[i - 3][1], pitch[i - 4][1]):
                if pitch[i][1] > (midf0 * 1.8):
                    if self.are_close(pitch[i - 1][1], pitch[i][1] / 2.):
                        pitch[i][1] /= 2.
                    elif self.are_close(pitch[i - 1][1], pitch[i][1] / 4.):
                        pitch[i][1] /= 4.
                elif pitch[i][1] < (midf0 / 1.8):
                    if self.are_close(pitch[i - 1][1], pitch[i][1] * 2):
                        pitch[i][1] *= 2.
                    elif self.are_close(pitch[i - 1][1], pitch[i][1] * 4):
                        pitch[i][1] *= 4.

        return pitch

    @staticmethod
    def remove_extreme_values(pitch):
        pitch_series = [element[1] for element in pitch]
        pitch_max = max(pitch_series)
        pitch_mean = np.mean(pitch_series)
        pitch_std = np.std(pitch_series)

        n = list(np.histogram(pitch_series, 100))

        for i in range(0, len(n[1]) - 1):
            if n[0][i] == 0 and n[0][i + 1] == 0:
                if sum(n[0][0: i + 1]) > 0.9 * sum(n[0]):
                    pitch_max = (n[1][i] + n[1][i + 1]) / 2.

        pitch_max_cand = max(pitch_mean * 4., pitch_mean + (2 * pitch_std))
        pitch_max = min(pitch_max, pitch_max_cand)

        # max values filter
        for j in range(0, len(pitch)):
            if pitch[j][1] >= pitch_max:
                pitch[j][1] = 0
                pitch[j][2] = 0

        # min values filter
        pitch_min = pitch_mean / 4.
        for j in range(0, len(pitch)):
            if pitch[j][1] <= pitch_min:
                pitch[j][1] = 0
                pitch[j][2] = 0

        return pitch

    def filter_noise_region(self, pitch):
        for i in range(0, 3):

            for j in range(1, len(pitch) - 2):
                if not self.are_close(pitch[i - 1][1], pitch[i][1]) and \
                        self.are_close(pitch[i][1], pitch[i + 1][1]):
                    pitch[i][1] = 0
                    pitch[i][2] = 0

            for j in range(2, len(pitch) - 3):
                if not self.are_close(pitch[j - 2][1], pitch[j][1]) and \
                        not self.are_close(pitch[j - 1][1], pitch[j][1]) and \
                        not self.are_close(pitch[j + 1][1],
                                           pitch[j + 2][1]) and \
                        not self.are_close(pitch[j + 1][1], pitch[j + 3][1]):
                    pitch[j][1] = 0
                    pitch[j + 1][1] = 0

        for i in range(1, len(pitch) - 2):
            if not self.are_close(pitch[i - 1][1], pitch[i][1]) and \
                    not self.are_close(pitch[i][1], pitch[i + 1][1]) and \
                    not self.are_close(pitch[i + 1][1], pitch[i + 2][1]) and \
                    not self.are_close(pitch[i - 1][1], pitch[i + 1][1]) and \
                    not self.are_close(pitch[i][1], pitch[i + 2][1]) and \
                    not self.are_close(pitch[i - 1], pitch[i + 2][1]):
                pitch[i][1] = 0
                pitch[i][2] = 0
                pitch[i + 1][1] = 0
                pitch[i + 2][2] = 0

        return pitch

    def filter_chunks_by_energy(self, pitch):
        pitch_chunks = self.decompose_into_chunks(pitch=pitch)

        chunk_length = [len(element) for element in pitch_chunks]
        longest_chunk = pitch_chunks[chunk_length.index(max(chunk_length))]

        energy = [element[2] for element in longest_chunk]
        min_energy = (sum(energy) / len(energy)) / 6.

        for p_chk in pitch_chunks:
            temp_energy = [element[2] for element in p_chk]
            ave_energy = sum(temp_energy) / len(temp_energy)

            if ave_energy != 0 and (
                    len(p_chk) <= self.min_chunk_size or
                    ave_energy <= min_energy):
                for element in p_chk:
                    element[1] = 0
                    element[2] = 0
        pitch = self.recompose_chunks(pitch_chunks=pitch_chunks)
        return pitch

    def run(self, pitch):
        for element in pitch:
            if element[1] == 0 or element[1] == 0.:
                element[1] = 0.0

        pitch = self.correct_octave_errors_by_chunks(pitch)
        pitch = self.remove_extreme_values(pitch)

        pitch = self.correct_jumps(pitch)
        pitch = list(reversed(pitch))
        pitch = self.correct_jumps(pitch)
        pitch = list(reversed(pitch))

        pitch = self.filter_noise_region(pitch)

        pitch = self.correct_oct_error(pitch)
        pitch = list(reversed(pitch))
        pitch = self.correct_oct_error(pitch)
        pitch = list(reversed(pitch))

        pitch = self.correct_octave_errors_by_chunks(pitch)
        pitch = self.filter_chunks_by_energy(pitch)

        return pitch.tolist()

    def filter(self, pitch):
        return self.run(pitch)
