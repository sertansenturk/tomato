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

import warnings
from ..symbolic.symbtr.reader.mu2 import Mu2


class Mu2(object):
    @staticmethod
    def from_mu2_header(score_file, symbtr_name=None):
        return Mu2.read_header(score_file, symbtr_name=symbtr_name)

    @classmethod
    def validate_mu2_attribute(cls, score_attrib, attrib_dict, score_name):

        is_attr_valid = True
        if 'mu2_name' in score_attrib.keys():  # work
            try:  # usul
                mu2_name, is_attr_valid = cls._validate_mu2_usul(
                    score_attrib, attrib_dict, score_name)

                if not mu2_name:  # no matching variant
                    is_attr_valid = False
                    warn_str = u'{0!s}, {1!s}: The Mu2 attribute does not ' \
                               u'match.'.format(score_name,
                                                score_attrib['mu2_name'])
                    warnings.warn(warn_str.encode('utf-8'), stacklevel=2)

            except KeyError:  # makam, form
                is_attr_valid = cls._validate_mu2_makam_form(
                    score_attrib, attrib_dict, score_name)

        return is_attr_valid

    @staticmethod
    def _validate_mu2_makam_form(score_attrib, attrib_dict, score_name):
        mu2_name = attrib_dict['mu2_name']
        if not score_attrib['mu2_name'] == mu2_name:
            warn_str = u'{0!s}, {1!s}: The Mu2 attribute does not match.'.\
                format(score_name, score_attrib['mu2_name'])

            warnings.warn(warn_str.encode('utf-8'), stacklevel=2)
            return False

        return True

    @staticmethod
    def _validate_mu2_usul(score_attrib, attrib_dict, score_name):
        mu2_name = ''
        is_usul_valid = True
        for uv in attrib_dict['variants']:
            if uv['mu2_name'] == score_attrib['mu2_name']:
                mu2_name = uv['mu2_name']
                for v_key in ['mertebe', 'num_pulses']:
                    # found variant
                    if not uv[v_key] == score_attrib[v_key]:
                        is_usul_valid = False
                        warn_str = u'{0:s}, {1:s}: The {2:s} of the usul in ' \
                                   u'the score does not ' \
                                   u'match.'.format(score_name,
                                                    uv['mu2_name'], v_key)
                        warnings.warn(warn_str.encode('utf-8'), stacklevel=2)

                    return is_usul_valid, mu2_name

        return mu2_name, is_usul_valid
