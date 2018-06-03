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

import json
import warnings

import musicbrainzngs as mb
from six.moves.urllib.request import urlopen

from .attribute import Attribute
from .. import __version__
from ..io import IO

mb.set_useragent("tomato", __version__, "compmusic.upf.edu")


class Work(object):
    @classmethod
    def from_musicbrainz(cls, mbid, get_recording_rels=True,
                         print_warnings=None):
        included_rels = (['artist-rels', 'recording-rels']
                         if get_recording_rels else ['artist-rels'])
        work = mb.get_work_by_id(mbid, includes=included_rels)['work']

        metadata = {
            'makam': [], 'form': [], 'usul': [], 'title': work['title'],
            'mbid': mbid, 'composer': dict(), 'lyricist': dict(),
            'url': 'http://musicbrainz.org/work/' + mbid, 'language': ''}

        # assign makam, form, usul attributes to data
        cls._assign_makam_form_usul(metadata, mbid, work)

        # language
        cls._assign_language(metadata, work)

        # composer and lyricist
        cls._assign_composer_lyricist(metadata, work)

        # add recordings
        cls._assign_recordings(metadata, work)

        # add scores
        cls._add_symbtr_names(metadata, mbid)

        # warnings
        cls._check_warnings(metadata, print_warnings)

        return metadata

    @classmethod
    def _add_symbtr_names(cls, metadata, mbid):
        score_work = cls._read_symbtr_mbid_dict()
        metadata['scores'] = []
        for sw in score_work:
            if mbid in sw['uuid']:
                metadata['scores'].append(sw['name'])

    @classmethod
    def get_mbids_from_symbtr_name(cls, symbtr_name):
        mbids = []  # extremely rare but there can be more than one mbid
        for e in cls._read_symbtr_mbid_dict():
            if e['name'] == symbtr_name:
                mbids.append(e['uuid'])
        if not mbids:
            warnings.warn(u"No MBID returned for {0:s}".format(symbtr_name),
                          RuntimeWarning, )
        return mbids

    @staticmethod
    def _read_symbtr_mbid_dict():
        try:
            url = "https://raw.githubusercontent.com/MTG/SymbTr/master/" \
                  "symbTr_mbid.json"
            response = urlopen(url)
            return json.loads(response.read())
        except IOError:  # load local backup
            warnings.warn("symbTr_mbid.json is not found in the local "
                          "search path. Using the back-up "
                          "symbTr_mbid.json included in this repository.")
            return IO.load_music_data('symbTr_mbid')

    @classmethod
    def _check_warnings(cls, metadata, print_warnings=None):
        if print_warnings:
            cls._data_key_exists(metadata, dkey='makam')
            cls._data_key_exists(metadata, dkey='form')
            cls._data_key_exists(metadata, dkey='usul')
            cls._data_key_exists(metadata, dkey='composer')

            if 'language' in metadata.keys():  # language in MusicBrainz
                cls._check_lyricist(metadata)
            else:  # no lyrics information in MusicBrainz
                cls._check_language(metadata)

    @staticmethod
    def _check_language(metadata):
        if metadata['lyricist']:  # lyricist available
            warnings.warn(
                u'http://musicbrainz.org/work/{0:s} Language of the vocal '
                u'work is not entered!'.format(metadata['mbid']), stacklevel=2)
        else:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} Language is not '
                          u'entered!'.format(metadata['mbid']), stacklevel=2)

    @staticmethod
    def _check_lyricist(metadata):
        if metadata['language'] == "zxx":  # no lyrics
            if metadata['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'entered to the instrumental work!'.
                              format(metadata['mbid']), stacklevel=2)
        else:  # has lyrics
            if not metadata['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'not entered!'.format(metadata['mbid']),
                              stacklevel=2)

    @staticmethod
    def _data_key_exists(metadata, dkey):
        if not metadata[dkey]:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} {1:s} is not '
                          u'entered!'.format(metadata['mbid'], dkey.title()),
                          stacklevel=2)

    @staticmethod
    def _assign_recordings(metadata, work):
        metadata['recordings'] = []
        if 'recording-relation-list' in work.keys():
            for r in work['recording-relation-list']:
                metadata['recordings'].append(
                    {'mbid': r['recording']['id'],
                     'title': r['recording']['title']})

    @staticmethod
    def _assign_composer_lyricist(metadata, work):
        if 'artist-relation-list' in work.keys():
            for a in work['artist-relation-list']:
                if a['type'] in ['composer', 'lyricist']:
                    metadata[a['type']] = {'name': a['artist']['name'],
                                           'mbid': a['artist']['id']}

    @staticmethod
    def _assign_language(metadata, work):
        if 'language' in work.keys():
            metadata['language'] = work['language']

    @classmethod
    def _assign_makam_form_usul(cls, metadata, mbid, work):
        if 'attribute-list' in work.keys():
            w_attrb = work['attribute-list']
            for attr_name in ['makam', 'form', 'usul']:
                cls._assign_attribute(metadata, mbid, w_attrb, attr_name)

    @staticmethod
    def _assign_attribute(metadata, mbid, w_attrb, attrname):
        attr = [a['value'] for a in w_attrb
                if attrname.title() in a['attribute']]
        metadata[attrname] = [
            {'mb_attribute': m,
             'attribute_key': Attribute.get_key_from_musicbrainz_attribute(
                 m, attrname),
             'source': 'http://musicbrainz.org/work/' + mbid}
            for m in attr]
