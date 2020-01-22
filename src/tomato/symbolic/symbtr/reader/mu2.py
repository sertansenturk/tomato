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

import csv
import warnings

from ....metadata.symbtr import SymbTr as SymbTrMetadata
from .symbtr import SymbTrReader


class Mu2Reader(SymbTrReader):
    @classmethod
    def read(cls, score_file, symbtr_name=None):
        """
        Reader method for the SymbTr-mu2 scores. This method is not
        implemented yet.

        Parameters
        ----------
        score_file : str
            The path of the SymbTr score
        symbtr_name : str, optional
            The name of the score in SymbTr naming convention
            (makam--form--usul--name--composer).
        Returns
        ----------
        NotImplemented
        """
        if symbtr_name is None:
            symbtr_name = Mu2Reader.get_symbtr_name_from_filepath(score_file)

        return NotImplemented

    @classmethod
    def read_header(cls, score_file, symbtr_name=None):
        """
        Reads the header of the SymbTr-mu2 scores.

        Parameters
        ----------
        score_file : str
            The path of the SymbTr score
        symbtr_name : str, optional
            The name of the score in SymbTr naming convention
            (makam--form--usul--name--composer).
        Returns
        ----------
        dict
            A dictionary storing the symbtr extracted from the header
        list of str
            The names of the columns in the mu2 file
        bool
            True if the symbtr in the mu2 header is valid/consistent,
            False otherwise
        """
        if symbtr_name is None:
            symbtr_name = Mu2Reader.get_symbtr_name_from_filepath(score_file)

        makam_slug = symbtr_name.split('--')[0]
        with open(score_file, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter='\t')
            header_row = next(reader, None)

            header = dict()
            is_tempo_unit_valid = True
            is_key_sig_valid = True
            for row in reader:
                code = int(row[0])
                if code == 50:
                    is_key_sig_valid = Mu2Reader.read_makam_key_signature_row(
                        header, is_key_sig_valid, makam_slug, row, symbtr_name)
                elif code == 51:
                    header['usul'] = {'mu2_name': row[7],
                                      'mertebe': int(row[3]),
                                      'number_of_pulses': int(row[2])}
                elif code == 52:
                    is_tempo_unit_valid = cls._read_tempo_row(
                        row, symbtr_name, header, is_tempo_unit_valid)
                elif code == 56:
                    header['usul']['subdivision'] = {
                        'mertebe': int(row[3]),
                        'number_of_pulses': int(row[2])}
                elif code == 57:
                    header['form'] = {'mu2_name': row[7]}
                elif code == 58:
                    header['composer'] = {'mu2_name': row[7]}
                elif code == 59:
                    header['lyricist'] = {'mu2_name': row[7]}
                elif code == 60:
                    header['title'] = {'mu2_title': row[7]}
                elif code == 62:
                    header['genre'] = 'folk' if row[7] == 'E' else 'classical'
                elif code == 63:
                    header['notation'] = row[7]
                elif code in range(50, 64):
                    warnings.warn('Unparsed code: {0!s}'.
                                  format(' '.join(row)), stacklevel=2)
                else:  # end of header
                    break

        # get the symbtr
        slugs = SymbTrMetadata.get_slugs(symbtr_name)
        for attr in ['makam', 'form', 'usul']:
            SymbTrMetadata.add_attribute_slug(header, slugs, attr)

        header['title']['symbtr_slug'] = slugs['name']
        header['composer']['symbtr_slug'] = slugs['composer']

        # validate the header content
        is_attr_meta_valid = SymbTrMetadata.validate_makam_form_usul(
            header, symbtr_name)

        is_header_valid = (is_tempo_unit_valid and is_attr_meta_valid and
                           is_key_sig_valid)

        return header, header_row, is_header_valid

    @staticmethod
    def read_makam_key_signature_row(header, is_key_sig_valid, makam_slug, row,
                                     symbtr_name):
        header['makam'] = {'mu2_name': row[7]}
        header['key_signature'] = row[8].split('/')
        if not header['key_signature'][0]:
            header['key_signature'] = []

        # validate key signature
        is_key_sig_valid = is_key_sig_valid and SymbTrMetadata. \
            validate_key_signature(header['key_signature'],
                                   makam_slug, symbtr_name)
        return is_key_sig_valid

    @staticmethod
    def _read_tempo_row(row, symbtr_name, header, is_tempo_unit_valid):
        try:
            header['tempo'] = {'value': int(row[4]),
                               'unit': 'bpm'}
        except ValueError:
            # the bpm might be a float for low tempo
            header['tempo'] = {'value': float(row[4]),
                               'unit': 'bpm'}

        if not (int(row[3]) == header['usul']['mertebe'] or
                header['usul']['mu2_name'] == '[Serbest]'):
            warnings.warn('{0!s}: Mertebe and tempo unit are different!'.
                          format(symbtr_name), stacklevel=2)
            is_tempo_unit_valid = False

        return is_tempo_unit_valid
