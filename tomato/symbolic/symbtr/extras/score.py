# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import urllib
import subprocess
import warnings
from ..dataextractor import DataExtractor
from ..reader.mu2 import Mu2Reader
from ....io import IO


class Score(object):
    @staticmethod
    def _read_symbtr_mbid():
        try:
            url = "https://raw.githubusercontent.com/MTG/SymbTr/master/" \
                  "symbTr_mbid.json"
            response = urllib.urlopen(url)
            return json.loads(response.read())
        except IOError:  # load local backup
            warnings.warn("symbtr_mbid.json is not found in the local "
                          "search path. Using the back-up "
                          "symbtr_mbid.json included in this repository.")
            return IO.load_music_data('symbTr_mbid')

    _iconv_map = {'utf-16le': 'UTF-16',
                  'Little-endian UTF-16 Unicode': 'UTF-16',
                  'iso-8859-1': 'ISO_8859-9', 'ISO-8859': 'ISO_8859-9'}

    @staticmethod
    def get_symbtr_data(txt_file, mu2_file):
        extractor = DataExtractor()
        txt_data = extractor.extract(txt_file)[0]

        mu2_header = Mu2Reader.read_header(mu2_file)[0]

        return extractor.merge(txt_data, mu2_header, verbose=False)

    @classmethod
    def get_mbids(cls, symbtr_name):
        mbids = []  # extremely rare but there can be more than one mbid
        for e in cls._read_symbtr_mbid():
            if e['name'] == symbtr_name:
                mbids.append(e['uuid'])
        return mbids

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

    @staticmethod
    def change_to_unix_linebreak(score_file):
        # change the line break from \r\n to \n
        try:  # linux
            subprocess.check_call("fromdos " + score_file, shell=True)
        except subprocess.CalledProcessError:  # mac
            subprocess.check_call("sed -e 's/\r$//' " + score_file +
                                  " > tmp.txt " + "&& mv -f tmp.txt " +
                                  score_file, shell=True)

    @classmethod
    def change_encoding_to_utf8(cls, score_file):
        try:  # unix
            out = subprocess.check_output("file -i " + score_file, shell=True)
            curr_charset = out.split('charset=')[1]

            if curr_charset.endswith('\n'):
                curr_charset = curr_charset[:-1]

            if not any(curr_charset in charset for charset in ['utf-8',
                                                               'us-ascii']):
                print(curr_charset + '\t' + score_file)
                commandstr = ("iconv -f " + cls._iconv_map[curr_charset] +
                              " -t UTF-8 " + score_file + " > tmp.txt "
                              "&& mv -f tmp.txt " + score_file)
                subprocess.check_output(commandstr, shell=True)
        except IndexError:  # mac
            raise OSError('Call this method in Linux for reliable results.')
