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
from ..io import IO

logger = logging.Logger(__name__, level=logging.INFO)


class Attribute(object):
    @staticmethod
    def get_attr_key_from_mb_attr(attr_str, attr_type):
        attr_dict = IO.load_music_data(attr_type)
        for attr_key, attr_val in attr_dict.items():
            if attr_val['dunya_name'] == attr_str:
                return attr_key

    @staticmethod
    def _get_attr_key_from_mb_tag(attr_str, attr_type):
        attr_dict = IO.load_music_data(attr_type)
        for attr_key, attr_val in attr_dict.items():
            if attr_str in attr_val['mb_tag']:
                return attr_key

    @classmethod
    def get_attrib_tags(cls, meta):
        theory_attribute_keys = ['makam', 'form', 'usul']
        attributes = dict()
        if 'tag-list' in meta.keys():
            for k in theory_attribute_keys:  # for makam/form/usul keys
                for t in meta['tag-list']:  # for each tag
                    try:  # attempt to assign the tag to the attribute key
                        cls._assign_attrib(attributes, k, t)
                    except ValueError:
                        logger.debug(u'{0:s} is not a makam/form/usul tag; '
                                     u'skipped'.format(t))
        return attributes

    @classmethod
    def _assign_attrib(cls, attributes, k, t):
        key, val = t['name'].split(': ')
        if k in key:
            if k not in attributes.keys():  # create the key
                attributes[k] = []

            attributes[k].append(
                {'mb_tag': val, 'attribute_key':
                    cls._get_attr_key_from_mb_tag(val, k)})
