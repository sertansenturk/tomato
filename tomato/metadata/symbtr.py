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

import codecs
import json
import warnings
from urllib.request import urlopen

from ..io import IO
from .musicbrainz import MusicBrainz


class SymbTr:
    @classmethod
    def from_musicbrainz(cls, score_name, mbid=None):
        metadata = MusicBrainz.crawl(mbid)

        # assign score name
        metadata['symbtr_name'] = score_name

        slugs = cls.get_slugs(score_name)
        for attr in ['makam', 'form', 'usul']:
            cls.add_attribute_slug(metadata, slugs, attr)

        if 'work' in metadata.keys():
            metadata['work']['symbtr_slug'] = slugs['name']
        elif 'recording' in metadata.keys():
            metadata['recording']['symbtr_slug'] = slugs['name']

        if 'composer' in metadata.keys():
            metadata['composer']['symbtr_slug'] = slugs['composer']

        # get and validate the attributes
        is_attrib_meta_valid = cls.validate_makam_form_usul(
            metadata, score_name)

        # get the tonic
        makam = cls._get_attribute(metadata['makam']['symbtr_slug'], 'makam')
        metadata['tonic'] = makam['karar_symbol']

        return metadata, is_attrib_meta_valid

    @staticmethod
    def get_slugs(symbtr_name):
        split = symbtr_name.split('--')

        return {'makam': split[0], 'form': split[1], 'usul': split[2],
                'name': split[3], 'composer': split[4]}

    @classmethod
    def add_attribute_slug(cls, data, slugs, attr):
        if attr in slugs.keys():
            if attr not in data.keys():
                data[attr] = {}
            data[attr]['symbtr_slug'] = slugs[attr]
            data[attr]['attribute_key'] = cls._get_attribute_key(
                data[attr]['symbtr_slug'], attr)

    @staticmethod
    def _get_attribute_key(attr_str, attr_type):
        attr_dict = IO.load_music_data(attr_type)
        for attr_key, attr_val in attr_dict.items():
            if attr_val['symbtr_slug'] == attr_str:
                return attr_key

    @classmethod
    def validate_key_signature(cls, key_signature, makam_slug, symbtr_name):
        attr_dict = IO.load_music_data('makam')
        key_sig_makam = attr_dict[makam_slug]['key_signature']

        # the number of accidentals should be the same
        is_key_sig_valid = len(key_signature) == len(key_sig_makam)

        # the sequence should be the same, allow a single comma deviation
        # due to AEU theory and practice mismatch
        for k1, k2 in zip(key_signature, key_sig_makam):
            is_key_sig_valid = (is_key_sig_valid and
                                cls._compare_accidentals(k1, k2))

        if not is_key_sig_valid:
            warnings.warn('{0!s}: Key signature is different! {1!s} -> {2!s}'.
                          format(symbtr_name, ' '.join(key_signature),
                                 ' '.join(key_sig_makam)), stacklevel=2)

        return is_key_sig_valid

    @staticmethod
    def _compare_accidentals(acc1, acc2):
        same_acc = True
        if acc1 == acc2:  # same note
            pass
        elif acc1[:3] == acc2[:3]:  # same note symbol
            if abs(int(acc1[3:]) - int(acc2[3:])) <= 1:  # 1 comma deviation
                pass
            else:  # more than one comma deviation
                same_acc = False
        else:  # different notes
            same_acc = False

        return same_acc

    @classmethod
    def validate_makam_form_usul(cls, data, score_name):
        is_valid_list = []
        for attr in ['makam', 'form', 'usul']:
            is_valid_list.append(cls._validate_attributes(
                data, score_name, attr))

        return all(is_valid_list)

    @classmethod
    def _validate_attributes(cls, data, score_name, attrib_name):
        score_attrib = data[attrib_name]

        attrib_dict = cls._get_attribute(score_attrib['symbtr_slug'],
                                         attrib_name)

        slug_valid = cls._validate_slug(
            attrib_dict, score_attrib, score_name)

        mu2_valid = cls._validate_mu2_attribute(
            score_attrib, attrib_dict, score_name)

        mb_attr_valid = cls._validate_musicbrainz_attribute(
            attrib_dict, score_attrib, score_name)

        mb_tag_valid = cls._validate_musicbrainz_attribute_tag(
            attrib_dict, score_attrib, score_name)

        return all([slug_valid, mu2_valid, mb_attr_valid, mb_tag_valid])

    @staticmethod
    def _validate_slug(attrib_dict, score_attrib, score_name):
        has_slug = 'symbtr_slug' in score_attrib.keys()

        not_valid = (
            has_slug
            and score_attrib['symbtr_slug'] != attrib_dict['symbtr_slug'])
        if not_valid:
            warnings.warn('{0!s}, {1!s}: The slug does not match.'.
                          format(score_name, score_attrib['symbtr_slug']),
                          stacklevel=2)
            return False

        return True

    @classmethod
    def _validate_mu2_attribute(cls, score_attrib, attrib_dict, score_name):
        is_attrib_valid = True
        if 'mu2_name' in score_attrib.keys():  # work
            try:  # usul
                mu2_name, is_attrib_valid = cls._validate_mu2_usul(
                    score_attrib, attrib_dict, score_name)

                if not mu2_name:  # no matching variant
                    is_attrib_valid = False
                    warn_str = '{0!s}, {1!s}: The Mu2 attribute does not ' \
                               'match.'.format(score_name,
                                               score_attrib['mu2_name'])
                    warnings.warn(warn_str.encode('utf-8'), stacklevel=2)

            except KeyError:  # makam, form
                is_attrib_valid = cls._validate_mu2_makam_form(
                    score_attrib, attrib_dict, score_name)

        return is_attrib_valid

    @staticmethod
    def _validate_mu2_makam_form(score_attrib, attrib_dict, score_name):
        mu2_name = attrib_dict['mu2_name']
        if not score_attrib['mu2_name'] == mu2_name:
            warn_str = '{0!s}, {1!s}: The Mu2 attribute does not match.'.\
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
                        warn_str = '{0:s}, {1:s}: The {2:s} of the usul in ' \
                                   'the score does not ' \
                                   'match.'.format(score_name,
                                                   uv['mu2_name'], v_key)
                        warnings.warn(warn_str.encode('utf-8'), stacklevel=2)

                    return is_usul_valid, mu2_name

        return mu2_name, is_usul_valid

    @staticmethod
    def _validate_musicbrainz_attribute(attrib_dict, score_attrib, score_name):
        is_attribute_valid = True
        if 'mb_attribute' in score_attrib.keys():  # work
            skip_makam_slug = ['12212212', '22222221', '223', '232223', '262',
                               '3223323', '3334', '14_4']
            if score_attrib['symbtr_slug'] in skip_makam_slug:
                warnings.warn('{0:s}: The usul attribute is not stored in '
                              'MusicBrainz.'.format(score_name), stacklevel=2)
            else:
                if not score_attrib['mb_attribute'] == \
                        attrib_dict['dunya_name']:
                    # dunya_names are (or should be) a superset of the
                    # musicbrainz attributes
                    is_attribute_valid = False
                    if score_attrib['mb_attribute']:
                        warn_str = '{0:s}, {1:s}: The MusicBrainz ' \
                                   'attribute does not match.' \
                                   ''.format(score_name,
                                             score_attrib['mb_attribute'])

                        warnings.warn(warn_str.encode('utf-8'), stacklevel=2)
                    else:
                        warnings.warn('{0:s}: The MusicBrainz attribute does'
                                      ' not exist.'.format(score_name),
                                      stacklevel=2)
        return is_attribute_valid

    @staticmethod
    def _validate_musicbrainz_attribute_tag(
            attrib_dict, score_attrib, score_name):
        is_attribute_valid = True
        has_mb_tag = 'mb_tag' in score_attrib.keys()
        if has_mb_tag and score_attrib['mb_tag'] not in attrib_dict['mb_tag']:
            is_attribute_valid = False

            warn_str = '{0!s}, {1!s}: The MusicBrainz tag does not match.'.\
                format(score_name, score_attrib['mb_tag'])

            warnings.warn(warn_str.encode('utf-8'), stacklevel=2)
        return is_attribute_valid

    @staticmethod
    def _get_attribute(slug, attribute_name):
        attribute_dict = IO.load_music_data(attribute_name)

        for attrib in attribute_dict.values():
            if attrib['symbtr_slug'] == slug:
                return attrib

        # no match
        return {}

    @classmethod
    def get_mbids_from_symbtr_name(cls, symbtr_name):
        mbids = []  # extremely rare but there can be more than one mbid
        for e in cls._read_symbtr_mbid_dict():
            if e['name'] == symbtr_name:
                mbids.append(e['uuid'])
        if not mbids:
            warnings.warn("No MBID returned for {0:s}".format(symbtr_name),
                          RuntimeWarning, )
        return mbids

    @classmethod
    def get_symbtr_names_from_mbid(cls, mbid):
        score_work = cls._read_symbtr_mbid_dict()
        symbtr_names = []
        for sw in score_work:
            if mbid in sw['uuid']:
                symbtr_names.append(sw['name'])

        return symbtr_names

    @staticmethod
    def _read_symbtr_mbid_dict():
        try:
            url = "https://raw.githubusercontent.com/MTG/SymbTr/master/" \
                  "symbTr_mbid.json"

            response = urlopen(url)
            reader = codecs.getreader("utf-8")

            return json.load(reader(response))
        except IOError:  # load local backup
            warnings.warn("Cannot reach github to read the latest "
                          "symbtr_mbid.json. Using the back-up "
                          "symbTr_mbid.json included in this repository.")
            return IO.load_music_data('symbTr_mbid')
