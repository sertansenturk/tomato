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

import logging
logger = logging.Logger(__name__, level=logging.INFO)


class Instrumentation(object):
    """
    This class decides the instrumentation (incl. vocal instrumentation) of an
    audio recording from the related artists
    """
    @classmethod
    def get_instrumentation(cls, audio_meta):
        instrument_vocal_list = []
        for a in audio_meta['artists']:
            choir_bool = (a['type'] == 'vocal' and
                          'attribute-list' in a.keys() and
                          'choir_vocals' in a['attribute-list'])
            if choir_bool:
                instrument_vocal_list.append(a['attribute-list'])
            elif a['type'] in ['conductor']:
                pass
            else:
                instrument_vocal_list.append(a['type'])

        # remove attributes, which are not about performance
        for ii, iv in reversed(list(enumerate(instrument_vocal_list))):
            if iv not in ['vocal', 'instrument', 'performing orchestra',
                          'performer', 'choir_vocals']:
                logger.info(u"{} is not related to instrumentation.".format(
                    iv))
                instrument_vocal_list.pop(ii)

        return cls._identify_instrumentation(instrument_vocal_list)

    @classmethod
    def _identify_instrumentation(cls, instrument_vocal_list):
        if cls.solo_instrumental(instrument_vocal_list):
            return "solo instrumental"
        elif cls.duo_instrumental(instrument_vocal_list):
            return "duo instrumental"
        elif cls.trio_instrumental(instrument_vocal_list):
            return "trio instrumental"
        elif cls.ensemble(instrument_vocal_list):
            return "ensemble instrumental"
        elif cls.solo_vocal_wo_acc(instrument_vocal_list):
            return "solo vocal without accompaniment"
        elif cls.solo_vocal_w_acc(instrument_vocal_list):
            return "solo vocal with accompaniment"
        elif cls.duet(instrument_vocal_list):
            return "duet"
        elif cls.choir(instrument_vocal_list):
            return "choir"
        else:
            assert False, "Unidentified instrumentation"

    # Solo Vocal Without Accompaniment
    # There is only vocal and no instruments
    @staticmethod
    def solo_vocal_wo_acc(instrument_vocal_list):
        return (len(instrument_vocal_list) == 1
                and instrument_vocal_list[0] == 'vocal')

    # Solo Vocal With Accompaniment
    # There is only one vocal and at least one instrument
    @staticmethod
    def solo_vocal_w_acc(instrument_vocal_list):
        return (len(instrument_vocal_list) > 1
                and instrument_vocal_list.count('vocal') == 1)

    # Duet With Accompaniment
    # There are two vocals and at least one instrument
    @staticmethod
    def duet(instrument_vocal_list):
        return (instrument_vocal_list.count('vocal') == 2
                and 'choir_vocals' not in instrument_vocal_list)

    # Choir With Accompaniment
    # There are more than 2 vocals and at least one instrument
    @staticmethod
    def choir(instrument_vocal_list):
        return (instrument_vocal_list.count('vocal') > 2
                or 'choir_vocals' in instrument_vocal_list)

    # Solo Instrumental
    # There is no vocal and only one instrument
    @staticmethod
    def solo_instrumental(instrument_vocal_list):
        return (
            len(instrument_vocal_list) == 1
            and instrument_vocal_list[0] in ['instrument', 'performer'])

    # Duo Instrumental
    # There is no vocal and only two instruments
    @staticmethod
    def duo_instrumental(instrument_vocal_list):
        return (len(instrument_vocal_list) == 2
                and all(iv in ['instrument', 'performer']
                        for iv in instrument_vocal_list))

    # Trio Instrumental
    # There is no vocal and only three instruments
    @staticmethod
    def trio_instrumental(instrument_vocal_list):
        return (len(instrument_vocal_list) == 3
                and all(iv in ['instrument', 'performer']
                        for iv in instrument_vocal_list))

    # Ensemble
    # There is no vocal and (many instruments OR an orchestra relation)
    @staticmethod
    def ensemble(instrument_vocal_list):
        return ('vocal' not in instrument_vocal_list
                and 'choir_vocals' not in instrument_vocal_list
                and ('performing orchestra' in instrument_vocal_list
                     or len(instrument_vocal_list) > 3))

    @classmethod
    def check_instrumentation_voice(cls, instrument_vocal_list):
        # remove attributes, which are not about performance
        for ii, iv in reversed(list(enumerate(instrument_vocal_list))):
            if iv not in ['vocal', 'instrument', 'performing orchestra',
                          'performer', 'choir_vocals']:
                logging.info(u"{} is not related to performance.".format(iv))
                instrument_vocal_list.pop(ii)

        if cls.solo_instrumental(instrument_vocal_list):
            return "solo instrumental"
        elif cls.duo_instrumental(instrument_vocal_list):
            return "duo instrumental"
        elif cls.trio_instrumental(instrument_vocal_list):
            return "trio instrumental"
        elif cls.ensemble(instrument_vocal_list):
            return "ensemble instrumental"
        elif cls.solo_vocal_wo_acc(instrument_vocal_list):
            return "solo vocal without accompaniment"
        elif cls.solo_vocal_w_acc(instrument_vocal_list):
            return "solo vocal with accompaniment"
        elif cls.duet(instrument_vocal_list):
            return "duet"
        elif cls.choir(instrument_vocal_list):
            return "choir"
        else:
            assert False, "Unidentified voicing/instrumentation"

    @classmethod
    def get_voicing_instrumentation(cls, audio_meta):
        vocal_instrument = []
        for a in audio_meta['artists']:
            choir_bool = (a['type'] == 'vocal'
                          and 'attribute-list' in a.keys()
                          and 'choir_vocals' in a['attribute-list'])
            if choir_bool:
                vocal_instrument.append(a['attribute-list'])
            elif a['type'] in ['conductor']:
                pass
            else:
                vocal_instrument.append(a['type'])

        return cls.check_instrumentation_voice(vocal_instrument)
