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
import musicbrainzngs
from six.moves.urllib.parse import urlparse
from ..recording import Recording as RecordingMetadata
from ..work import Work as WorkMetadata


class MusicBrainz(object):
    @classmethod
    def crawl_musicbrainz(cls, mbid):
        if mbid is None:  # empty mbid
            return {'makam': {}, 'form': {}, 'usul': {}, 'name': {},
                    'composer': {}, 'lyricist': {}}

        try:  # attempt crawling
            mbid = cls._parse_mbid(mbid)
            try:  # assume mbid is a work
                data = WorkMetadata.from_musicbrainz(mbid)
                data['work'] = {'title': data.pop("title", None),
                                'mbid': data.pop('mbid', None)}
            except musicbrainzngs.ResponseError:  # assume mbid is a recording
                data = RecordingMetadata.from_musicbrainz(mbid)
                data['recording'] = {'title': data.pop("title", None),
                                     'mbid': data.pop('mbid', None)}

            cls._add_musicbrainz_attributes(data)
            return data
        except musicbrainzngs.NetworkError:
            warnings.warn("Musicbrainz is not available, cannot crawl "
                          "metadata...", stacklevel=2)
            return {'makam': {}, 'form': {}, 'usul': {}, 'name': {},
                    'composer': {}, 'lyricist': {}, 'url': ''}

    @staticmethod
    def _add_musicbrainz_attributes(data):
        # scores should have one attribute per type
        for attr in ['makam', 'form', 'usul']:
            try:
                data[attr] = data[attr][0]
            except (IndexError, KeyError):
                warnings.warn(
                    "Missing the {0:s} attribute in MusicBrainz".format(attr),
                    stacklevel=2)
                data.pop(attr, None)

    @staticmethod
    def _parse_mbid(mbid):
        o = urlparse(mbid)

        # if the url is given get the mbid, which is the last field
        o_splitted = o.path.split('/')
        mbid = o_splitted[-1]

        return mbid

    @staticmethod
    def validate_musicbrainz_attribute(attrib_dict, score_attrib, scorename):
        is_attribute_valid = True
        if 'mb_attribute' in score_attrib.keys():  # work
            skip_makam_slug = ['12212212', '22222221', '223', '232223', '262',
                               '3223323', '3334', '14_4']
            if score_attrib['symbtr_slug'] in skip_makam_slug:
                warnings.warn(u'{0:s}: The usul attribute is not stored in '
                              u'MusicBrainz.'.format(scorename), stacklevel=2)
            else:
                if not score_attrib['mb_attribute'] == \
                        attrib_dict['dunya_name']:
                    # dunya_names are (or should be) a superset of the
                    # musicbrainz attributes
                    is_attribute_valid = False
                    if score_attrib['mb_attribute']:
                        warn_str = u'{0:s}, {1:s}: The MusicBrainz ' \
                                   u'attribute does not match.' \
                                   u''.format(scorename,
                                              score_attrib['mb_attribute'])

                        warnings.warn(warn_str.encode('utf-8'), stacklevel=2)
                    else:
                        warnings.warn(u'{0:s}: The MusicBrainz attribute does'
                                      u' not exist.'.format(scorename),
                                      stacklevel=2)
        return is_attribute_valid

    @staticmethod
    def validate_musicbrainz_attribute_tag(
            attrib_dict, score_attrib, scorename):
        is_attribute_valid = True
        has_mb_tag = 'mb_tag' in score_attrib.keys()
        if has_mb_tag and score_attrib['mb_tag'] not in attrib_dict['mb_tag']:
            is_attribute_valid = False

            warn_str = u'{0!s}, {1!s}: The MusicBrainz tag does not match.'.\
                format(scorename, score_attrib['mb_tag'])

            warnings.warn(warn_str.encode('utf-8'), stacklevel=2)
        return is_attribute_valid
