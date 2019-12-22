#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2015 - 2018 Altuğ Karakurt & Sertan Şentürk
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
# Karakurt, A., Şentürk S., and Serra X. (2016). MORTY: A toolbox for mode
# recognition and tonic identification. In Proceedings of 3rd International
# Digital Libraries for Musicology Workshop (DLfM 2016). pages 9-16,
# New York, NY, USA

from typing import Union

import numpy as np

_NUM_CENTS_IN_OCTAVE = 1200.0


class Converter:
    @staticmethod
    def hz_to_cent(hz_track: Union[list, np.array],
                   ref_freq: Union[float, np.float],
                   min_freq: Union[float, np.float] = 20.0
                   ) -> np.array:
        """--------------------------------------------------------------------
        Converts an array of Hertz values into cents.
        -----------------------------------------------------------------------
        hz_track : The 1-D array of Hertz values
        ref_freq : Reference frequency for cent conversion
        min_freq : The minimum frequency allowed (exclusive)
        --------------------------------------------------------------------"""

        if ref_freq < 0:
            raise ValueError("ref_freq cannot be negative.")
        if min_freq < 0:
            raise ValueError("min_freq cannot be negative.")
        if ref_freq < min_freq:
            raise ValueError("ref_freq cannot be less than min_freq.")

        hz_track = np.array(hz_track).astype(float)
        if (hz_track < 0).any():
            raise ValueError("hz_track cannot be negative values.")

        # change values less than the min_freq to nan
        hz_track[hz_track <= min_freq] = np.nan

        return np.log2(hz_track / ref_freq) * _NUM_CENTS_IN_OCTAVE

    @staticmethod
    def cent_to_hz(cent_track: np.array,
                   ref_freq: np.float
                   ) -> np.array:
        """--------------------------------------------------------------------
        Converts an array of cent values into Hertz.
        -----------------------------------------------------------------------
        cent_track  : The 1-D array of cent values
        ref_freq    : Reference frequency for cent conversion
        --------------------------------------------------------------------"""
        cent_track = np.array(cent_track).astype(float)

        return 2 ** (cent_track / _NUM_CENTS_IN_OCTAVE) * ref_freq
