#!/usr/bin/env python


# Copyright 2016 Sertan Şentürk
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

from ..converter import Converter
from ..io import IO


class Ahenk:
    CENTS_IN_OCTAVE = 1200  # cents

    @classmethod
    def identify(cls, tonic_freq, symbol_in):
        assert 20.0 <= tonic_freq <= 20000.0, "The input tonic frequency " \
                                              "must be between and 20000 Hz"

        tonic_dict = IO.load_music_data('tonic')
        ahenks = IO.load_music_data('ahenk')

        # get the tonic symbol and frequency
        tonic_symbol, tonic_bolahenk_freq, makam = cls._get_tonic_symbol(
            symbol_in, tonic_dict)

        # get the transposition in cents, rounded to the closest semitone
        cent_dist = Converter.hz_to_cent(tonic_freq, tonic_bolahenk_freq)
        mod_cent_dist = np.mod(cent_dist, cls.CENTS_IN_OCTAVE)

        # if the distance is more than 1150 cents wrap it to minus
        # so it will be mapped to 0 cents
        mod_cent_dist = (mod_cent_dist if mod_cent_dist < 1150
                         else mod_cent_dist - 1200)

        mod_cent_approx = int(np.round(mod_cent_dist * 0.01) * 100)
        mod_cent_dev = mod_cent_approx - mod_cent_dist
        abs_mod_cent_dev = abs(mod_cent_dev)

        # create the stats dictionary
        distance_to_bolahenk = {
            'performed': {'value': mod_cent_dist, 'unit': 'cent'},
            'theoretical': {'value': mod_cent_approx, 'unit': 'cent'}}
        ahenk_dict = {'name': '', 'slug': '', 'makam': makam,
                      'tonic_symbol': tonic_symbol,
                      'distance_to_bolahenk': distance_to_bolahenk,
                      'deviation': {'value': mod_cent_dev,
                                    'unit': 'cent'},
                      'abs_deviation': {'value': abs_mod_cent_dev,
                                        'unit': 'cent'}}

        # get the ahenk
        for ahenk_slug, val in ahenks.items():
            if val['cent_transposition'] == mod_cent_approx:
                ahenk_dict['name'] = val['name']
                ahenk_dict['slug'] = ahenk_slug
                return ahenk_dict

    @classmethod
    def _get_tonic_symbol(cls, symbol_in, tonic_dict):
        if symbol_in in tonic_dict.keys():  # tonic symbol given
            tonic_symbol = symbol_in
            makam = None
            tonic_bolahenk_freq = tonic_dict[symbol_in]['bolahenk_freq']
        else:  # check if the makam name is given
            makam = symbol_in
            tonic_symbol, tonic_bolahenk_freq = \
                cls._get_tonic_symbol_from_makam(symbol_in, tonic_dict)
            if not tonic_bolahenk_freq:
                raise ValueError("The second input has to be a tonic symbol "
                                 "or a makam slug!")

        return tonic_symbol, tonic_bolahenk_freq, makam

    @staticmethod
    def _get_tonic_symbol_from_makam(symbol_in, tonic_dict):
        tonic_bolahenk_freq = tonic_symbol = None
        for sym, val in tonic_dict.items():
            if symbol_in in val['makams']:
                tonic_symbol = sym
                tonic_bolahenk_freq = val['bolahenk_freq']
                if not tonic_bolahenk_freq:  # tonic symbol is not known
                    raise KeyError("The tonic of this makam is not known.")
                break
        return tonic_symbol, tonic_bolahenk_freq
