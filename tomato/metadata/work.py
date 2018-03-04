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
from six.moves.urllib.request import urlopen
from . attribute import Attribute
from ..io import IO
from .. import __version__

import musicbrainzngs as mb
mb.set_useragent("tomato_toolbox", __version__, "compmusic.upf.edu")


class Work(object):
    def __init__(self, print_warnings=None):
        self.print_warnings = print_warnings

    def from_musicbrainz(self, mbid, get_recording_rels=True):
        included_rels = (['artist-rels', 'recording-rels']
                         if get_recording_rels else ['artist-rels'])
        work = mb.get_work_by_id(mbid, includes=included_rels)['work']

        data = {'makam': [], 'form': [], 'usul': [], 'title': work['title'],
                'mbid': mbid, 'composer': dict(), 'lyricist': dict(),
                'url': 'http://musicbrainz.org/work/' + mbid, 'language': ''}

        # assign makam, form, usul attributes to data
        self._assign_makam_form_usul(data, mbid, work)

        # language
        self._assign_language(data, work)

        # composer and lyricist
        self._assign_composer_lyricist(data, work)

        # add recordings
        self._assign_recordings(data, work)

        # add scores
        self._add_symbtr_names(data, mbid)

        # warnings
        self._check_warnings(data)

        return data

    @classmethod
    def _add_symbtr_names(cls, data, mbid):
        score_work = cls._read_symbtr_mbid_dict()
        data['scores'] = []
        for sw in score_work:
            if mbid in sw['uuid']:
                data['scores'].append(sw['name'])

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

    def _check_warnings(self, data):
        if self.print_warnings:
            self._data_key_exists(data, dkey='makam')
            self._data_key_exists(data, dkey='form')
            self._data_key_exists(data, dkey='usul')
            self._data_key_exists(data, dkey='composer')

            if 'language' in data.keys():  # language entered to MusicBrainz
                self._check_lyricist(data)
            else:  # no lyrics information in MusicBrainz
                self._check_language(data)

    @staticmethod
    def _check_language(data):
        if data['lyricist']:  # lyricist available
            warnings.warn(u'http://musicbrainz.org/work/{0:s} Language of the '
                          u'vocal work is not entered!'.format(data['mbid']),
                          stacklevel=2)
        else:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} Language is not '
                          u'entered!'.format(data['mbid']), stacklevel=2)

    @staticmethod
    def _check_lyricist(data):
        if data['language'] == "zxx":  # no lyrics
            if data['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'entered to the instrumental work!'.
                              format(data['mbid']), stacklevel=2)
        else:  # has lyrics
            if not data['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'not entered!'.format(data['mbid']),
                              stacklevel=2)

    @staticmethod
    def _data_key_exists(data, dkey):
        if not data[dkey]:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} {1:s} is not '
                          u'entered!'.format(data['mbid'], dkey.title()),
                          stacklevel=2)

    @staticmethod
    def _assign_recordings(data, work):
        data['recordings'] = []
        if 'recording-relation-list' in work.keys():
            for r in work['recording-relation-list']:
                data['recordings'].append({'mbid': r['recording']['id'],
                                           'title': r['recording']['title']})

    @staticmethod
    def _assign_composer_lyricist(data, work):
        if 'artist-relation-list' in work.keys():
            for a in work['artist-relation-list']:
                if a['type'] in ['composer', 'lyricist']:
                    data[a['type']] = {'name': a['artist']['name'],
                                       'mbid': a['artist']['id']}

    @staticmethod
    def _assign_language(data, work):
        if 'language' in work.keys():
            data['language'] = work['language']

    @classmethod
    def _assign_makam_form_usul(cls, data, mbid, work):
        if 'attribute-list' in work.keys():
            w_attrb = work['attribute-list']
            for attr_name in ['makam', 'form', 'usul']:
                cls._assign_attribute(data, mbid, w_attrb, attr_name)

    @staticmethod
    def _assign_attribute(data, mbid, w_attrb, attrname):
        attr = [a['value'] for a in w_attrb
                if attrname.title() in a['attribute']]
        data[attrname] = [
            {'mb_attribute': m,
             'attribute_key': Attribute.get_attr_key_from_mb_attr(m, attrname),
             'source': 'http://musicbrainz.org/work/' + mbid}
            for m in attr]
