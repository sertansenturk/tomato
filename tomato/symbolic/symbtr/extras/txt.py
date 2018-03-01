# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pandas as pd
import os
import warnings
from ..dataextractor import DataExtractor
from ..reader.mu2 import Mu2Reader
from ....io import IO


class Txt(object):
    symbtr_cols = ['Sira', 'Kod', 'Nota53', 'NotaAE', 'Koma53', 'KomaAE',
                   'Pay', 'Payda', 'Ms', 'LNS', 'Bas', 'Soz1', 'Offset']

    @classmethod
    def check_usul_row(cls, txt_file):
        mu2_usul_dict, inv_mu2_usul_dict = cls._parse_usul_dict()

        df = pd.read_csv(txt_file, sep='\t', encoding='utf-8')

        symbtr_name = os.path.splitext(txt_file)[0]

        for index, row in df.iterrows():
            # change null to empty string
            row_changed = cls._change_null_element_to_empty_str(row)

            if row['Kod'] == 51:
                row_changed = cls._parse_usul_row(
                    row, index, mu2_usul_dict, inv_mu2_usul_dict, symbtr_name,
                    row_changed)

            if row_changed:
                df.iloc[index] = row

        return df.to_csv(None, sep=b'\t', index=False, encoding='utf-8')

    @staticmethod
    def get_symbtr_data(txt_file, mu2_file):
        extractor = DataExtractor()
        txt_data = extractor.extract(txt_file)[0]

        mu2_header = Mu2Reader.read_header(mu2_file)[0]

        return extractor.merge(txt_data, mu2_header, verbose=False)

    @staticmethod
    def _parse_usul_dict():
        mu2_usul_dict = {}
        inv_mu2_usul_dict = {}
        usul_dict = IO.load_music_data('usul')
        for key, val in usul_dict.items():
            for vrt in val['variants']:
                if vrt['mu2_name']:  # if it doesn't have a mu2 name, the usul
                    # is not in symbtr collection
                    zaman = int(vrt['num_pulses']) if vrt['num_pulses'] else []
                    mertebe = int(vrt['mertebe']) if vrt['mertebe'] else []
                    if vrt['mu2_name'] in ['(Serbest)', '[Serbest]',
                                           'Serbest']:
                        zaman = 0
                        mertebe = 0
                    mu2_usul_dict[vrt['mu2_name']] = {
                        'id': int(vrt['symbtr_internal_id']), 'zaman': zaman,
                        'mertebe': mertebe}

                    inv_mu2_usul_dict[int(vrt['symbtr_internal_id'])] = {
                        'mu2_name': vrt['mu2_name'], 'zaman': zaman,
                        'mertebe': mertebe}
        return mu2_usul_dict, inv_mu2_usul_dict

    @classmethod
    def _parse_usul_row(cls, row, index, mu2_usul_dict, inv_mu2_usul_dict,
                        symbtr_name, row_changed):
        usul_id = row['LNS']
        usul_name = row['Soz1']
        if usul_name:  # name given
            cls._chk_usul_by_name(index, mu2_usul_dict, row, symbtr_name,
                                  usul_id, usul_name)
        elif usul_id:
            row_changed = cls._chk_usul_by_id(
                index, inv_mu2_usul_dict, row,
                symbtr_name, usul_id, usul_name, row_changed)
        else:
            raise RuntimeError("Unexpected operation")

        return row_changed

    @classmethod
    def _chk_usul_by_name(cls, index, mu2_usul_dict, row, symbtr_name, usul_id,
                          usul_name):
        # check if the usul pair matches with the mu2dict
        if usul_name in mu2_usul_dict and mu2_usul_dict[usul_name]['id'] == \
                usul_id:
            cls._chk_usul_attr(row, mu2_usul_dict[usul_name], 'zaman',
                               symbtr_name, index, usul_name)
            cls._chk_usul_attr(row, mu2_usul_dict[usul_name], 'mertebe',
                               symbtr_name, index, usul_name)
        else:
            warnstr = u'{0:s}, line {1:s}: {2:s} and {3:s} does not match.'.\
                format(symbtr_name, str(index), usul_name, str(usul_id))
            warnings.warn(warnstr.encode('utf-8'))

    @classmethod
    def _chk_usul_by_id(cls, index, inv_mu2_usul_dict, row, symbtr_name,
                        usul_id, usul_name, row_changed):
        if usul_id == -1:
            warnings.warn(u'{0:s}, line {1:s}: Missing usul info'.format(
                symbtr_name, str(index)).encode('utf-8'))
        else:
            warnstr = u'{0:s}, line {1:d}: Filling missing {2:s}'.format(
                symbtr_name, index, inv_mu2_usul_dict[usul_id]['mu2_name'])
            warnings.warn(warnstr.encode('utf-8'))
            row['Soz1'] = inv_mu2_usul_dict[usul_id]['mu2_name']

            cls._chk_usul_attr(row, inv_mu2_usul_dict[usul_id], 'zaman',
                               symbtr_name, index, usul_name)
            cls._chk_usul_attr(row, inv_mu2_usul_dict[usul_id], 'mertebe',
                               symbtr_name, index, usul_name)
            row_changed = True
        return row_changed

    @staticmethod
    def _change_null_element_to_empty_str(row):
        row_changed = False
        for key, val in row.items():
            if pd.isnull(val):
                row[key] = ''
                row_changed = True
        return row_changed

    @staticmethod
    def _chk_usul_attr(row, usul, attr_str, symbtr_name, index, usul_name):
        if attr_str == 'mertebe':
            row_str = 'Payda'
        elif attr_str == 'zaman':
            row_str = 'Pay'
        else:
            raise ValueError(
                u'Unexpected usul attribute: {0:s}'.format(attr_str))
        if not usul[attr_str] == row[row_str]:
            warnstr = u'{0:s}, line {1:s}: {2:s} and {3:s} does not match.'\
                .format(symbtr_name, str(index), usul_name, attr_str)
            warnings.warn(warnstr.encode('utf-8'))

    @classmethod
    def add_usul_to_first_row(cls, txt_file, mu2_file):
        # extract symbtr data
        data = cls.get_symbtr_data(txt_file, mu2_file)

        # get usul variant
        variant = cls._get_usul_variant(data)  # read the txt score
        df = pd.read_csv(txt_file, sep=b'\t')

        # create the usul row
        # 1    51            0    0    zaman    mertebe    0    usul_symbtr_internal_id    0    usul_mu2_name    0
        # 1    51            0    0    6    4    0    90    0    Yürüksemâî (6/4)    0
        usul_row = pd.DataFrame(
            {'Sira': 1, 'Kod': 51, 'Nota53': '', 'NotaAE': '', 'Koma53': 0,
             'KomaAE': 0, 'Pay': int(variant['num_pulses']),
             'Payda': int(variant['mertebe']), 'Ms': 0, 'Offset': 0,
             'LNS': variant['symbtr_internal_id'], 'Bas': 0,
             'Soz1': variant['mu2_name']}, index=[0])

        if not df.iloc[0]['Kod'] == 51:
            for index, row in df.iterrows():
                cls._change_null_to_empty_str(row)

                # make sure that "Sira" column continues consecutively
                row['Sira'] = index + 2  # 2 instead of 1, since we also add
                # the usul row to the start

                # reassign
                df.iloc[index] = row

            df_usul = pd.concat(
                [usul_row, df], ignore_index=True)[cls.symbtr_cols]
        else:
            if not df.iloc[0]["LNS"] == usul_row.iloc[0]["LNS"]:
                print(u"{0:s} starts with a different usul row. Correcting...".
                      format(data['symbtr']).encode('utf-8'))
                df_usul = pd.concat(
                    [usul_row, df.ix[1:]], ignore_index=True)[cls.symbtr_cols]
            else:
                print(u"{0:s} starts with the usul row. Skipping...".format(
                    data['symbtr']).encode('utf-8'))
                df_usul = df

        return df_usul.to_csv(None, sep=b'\t', index=False, encoding='utf-8')

    @classmethod
    def correct_offset_gracenote(cls, txt_file, mu2_file):
        # extract symbtr data
        data = cls.get_symbtr_data(txt_file, mu2_file)

        # get zaman and mertebe from usul variant
        mertebe, zaman = cls._get_zaman_mertebe(data)

        # correct the offsets and the gracenote durations
        df = pd.read_csv(txt_file, sep=b'\t')
        for index, row in df.iterrows():
            # recompute the erroneous gracenotes with non-zero duration
            if row['Kod'] == 8 and row['Ms'] > 0:
                row['Pay'] = 0
                row['Payda'] = 0
                row['Ms'] = 0

            # recompute zaman and mertebe, if we hit kod 51
            if row['Kod'] == 51:
                zaman = row['Pay']
                mertebe = row['Payda']
                offset_incr = 0
            else:
                # compute offset
                offset_incr = 0 if row['Payda'] == 0 else \
                    float(row['Pay']) / row['Payda'] * mertebe / zaman

            if index == 0:
                row['Offset'] = offset_incr
            else:
                prev_row = df.iloc[index - 1]
                row['Offset'] = offset_incr + prev_row['Offset']

            # change null to empty string
            cls._change_null_to_empty_str(row)

            # make sure that "Sira" column continues consecutively
            row['Sira'] = index + 1

            # reassign
            df.iloc[index] = row

        cls._check_premature_ending(row)

        return df.to_csv(None, sep=b'\t', index=False, encoding='utf-8')

    @staticmethod
    def correct_rests(txt_file):
        # correct the offsets and the gracenote durations
        df = pd.read_csv(txt_file, sep=b'\t')
        rest_list = [9, -1, -1, 'Es', 'Es']
        for index, row in df.iterrows():
            val_list = [row['Kod'], row['Koma53'], row['KomaAE'],
                        row['Nota53'], row['NotaAE']]

            # check if rest. If yes, check if valid
            is_rest = any(v1 == v2 for v1, v2 in
                          zip(val_list[1:], rest_list[1:]))
            is_invalid = any(v1 != v2 for v1, v2 in zip(val_list, rest_list))
            if is_rest and is_invalid:
                (row['Kod'], row['Koma53'], row['KomaAE'], row['Nota53'],
                 row['NotaAE']) = rest_list
                df.iloc[index] = row
        return df.to_csv(None, sep=b'\t', index=False, encoding='utf-8')

    @staticmethod
    def _check_premature_ending(row):
        # warn if the last measure end prematurely, i.e. the last note does not
        # have an integer offset
        if not (round(row['Offset'] * 10000) * 0.0001).is_integer():
            warnings.warn("Ends prematurely!")

    @staticmethod
    def _get_usul_variant(data):
        usul_dict = IO.load_music_data('usul')
        vrts = usul_dict[data['usul']['symbtr_slug']]['variants']
        for v in vrts:
            if v['mu2_name'] == data['usul']['mu2_name']:
                return v

        assert False, u'The usul variant {0:s} is not found'.format(
            data['usul']['mu2_name'])

    @staticmethod
    def _get_zaman_mertebe(data):
        usul_dict = IO.load_music_data('usul')
        for usul in usul_dict.values():
            for uv in usul['variants']:
                if uv['mu2_name'] == data['usul']['mu2_name']:
                    return uv['mertebe'], uv['num_pulses']

        assert False, u'Zaman and mertebe for the usul variant {0:s} is not ' \
                      u'available'.format(data['usul']['mu2_name'])

    @staticmethod
    def _change_null_to_empty_str(row):
        # change null to empty string
        for key, val in row.items():
            if pd.isnull(val):
                row[key] = ''
