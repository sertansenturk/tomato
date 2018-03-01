# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ..dataextractor import DataExtractor
from ..reader.mu2 import Mu2Reader
from ....io import IO


class Score(object):
    @staticmethod
    def get_symbtr_data(txt_file, mu2_file):
        extractor = DataExtractor()
        txt_data = extractor.extract(txt_file)[0]

        mu2_header = Mu2Reader.read_header(mu2_file)[0]

        return extractor.merge(txt_data, mu2_header, verbose=False)

    @classmethod
    def parse_usul_dict(cls):
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
