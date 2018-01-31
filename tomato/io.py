#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 Sertan Şentürk
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

import tempfile
import os
import pickle
import re
import unicodedata
import fnmatch
from six import iteritems
from json_tricks import np as json


class IO(object):
    @staticmethod
    def make_unicode(input_str):
        if not isinstance(input_str, unicode):
            if input_str is None:
                return None
            else:
                return input_str.decode('utf-8')
        else:
            return input_str

    @staticmethod
    def slugify_tr(str_val):
        value_slug = str_val.replace(u'\u0131', 'i')
        value_slug = unicodedata.normalize('NFKD', value_slug)
        value_slug = value_slug.encode('ascii', 'ignore').decode('ascii')
        value_slug = re.sub('[^\w\s-]', '', value_slug).strip()

        return re.sub('[-\s]+', '-', value_slug)

    @staticmethod
    def public_noncallables(inst):
        noncallable_gen = (v for v in dir(inst)
                           if not callable(getattr(inst, v)))
        return [name for name in noncallable_gen
                if not name.startswith('_')]

    @staticmethod
    def get_abspath_from_relpath_in_tomato(*args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

    @staticmethod
    def create_temp_file(extension, content_str, folder=None):
        fd, temp_path = tempfile.mkstemp(extension, dir=folder)
        open_mode = 'wb' if extension in ['.mat'] else 'w'
        with open(temp_path, open_mode) as f:
            f.write(content_str)
        os.close(fd)

        return temp_path

    @staticmethod
    def remove_temp_files(*argv):
        for path in argv:
            try:
                os.unlink(path)
            except OSError:  # directory
                os.rmdir(path)

    @staticmethod
    def load_json_from_temp_folder(temp_out_folder, expected):
        # load the results from the temporary folder
        out_dict = {}
        for exp in expected:
            fpath = os.path.join(temp_out_folder, exp + '.json')
            if os.path.isfile(fpath):
                out_dict[exp] = json.load(open(fpath))
                os.unlink(fpath)  # remove file created in the temporary folder
            else:
                raise Exception(u'Missing output {0:s} file'.format(exp))

        return out_dict

    # compiled regular expressions for dict_keys_to_snake_case
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @staticmethod
    def dict_keys_to_snake_case(camel_case_dict):
        sdict = {}
        try:
            for k, v in iteritems(camel_case_dict):
                key = IO.first_cap_re.sub(r'\1_\2', k)
                key = IO.all_cap_re.sub(r'\1_\2', key).lower()

                sdict[key] = IO.dict_keys_to_snake_case(v)
        except AttributeError:  # input is not a dict, return
            sdict = camel_case_dict

        return sdict

    @staticmethod
    def dict_keys_to_camel_case(snake_case_dict):
        cdict = {}
        try:
            for k, v in iteritems(snake_case_dict):
                components = k.split('_')
                key = "".join(x.title() for x in components)

                cdict[key] = IO.dict_keys_to_camel_case(v)
        except AttributeError:  # input is not a dict, return
            cdict = snake_case_dict

        return cdict

    @staticmethod
    def to_pickle(features, filepath=None):
        if filepath is None:
            return pickle.dumps(features)
        else:
            pickle.dump(features, open(filepath, 'wb'))

    @staticmethod
    def to_json(features, filepath=None):
        if filepath is None:
            return json.dumps(features, indent=4)
        else:
            json.dump(features, open(filepath, 'w'), indent=4)

    @staticmethod
    def from_pickle(input_str):
        try:  # file given
            return pickle.load(open(input_str, 'rb'))
        except IOError:  # string given
            return pickle.loads(input_str, 'rb')

    @staticmethod
    def from_json(input_str):
        try:  # file given
            return json.load(open(input_str), preserve_order=False)
        except IOError:  # string given
            return json.loads(input_str, 'r', preserve_order=False)

    @staticmethod
    def get_filenames_in_dir(dir_name, keyword='*', skip_foldername='',
                             match_case=True, verbose=False):
        """
        Args:
            dir_name (str): The foldername.
            keyword (str): The keyword to search (defaults to '*').
            skip_foldername (str): An optional foldername to skip searching
            match_case (bool): Flag for case matching
            verbose (bool): Verbosity flag
        Returns:
            (tuple): Tuple containing:
                - fullnames (list): List of the fullpaths of the files found
                - folder (list): List of the folders of the files
                - names (list): List of the filenames without the foldername
        Examples:
            >>> get_filenames_in_dir('/path/to/dir/', '*.mp3')  #doctest: +SKIP
            (['/path/to/dir/file1.mp3', '/path/to/dir/folder1/file2.mp3'], ['/path/to/dir/', '/path/to/dir/folder1'], ['file1.mp3', 'file2.mp3'])
        """
        names = []
        folders = []
        fullnames = []

        if verbose:
            print(dir_name)

        # check if the folder exists
        if not os.path.isdir(dir_name):
            if verbose:
                print("Directory doesn't exist!")
            return [], [], []

        # if the dir_name finishes with the file separator,
        # remove it so os.walk works properly
        dir_name = dir_name[:-1] if dir_name[-1] == os.sep else dir_name

        # walk all the subdirectories
        for (path, dirs, files) in os.walk(dir_name):
            for f in files:
                has_key = (fnmatch.fnmatch(f, keyword) if match_case else
                           fnmatch.fnmatch(f.lower(), keyword.lower()))
                if has_key and skip_foldername not in path.split(os.sep)[1:]:
                    try:
                        folders.append(unicode(path, 'utf-8'))
                    except TypeError:  # already unicode
                        folders.append(path)
                    try:
                        names.append(unicode(f, 'utf-8'))
                    except TypeError:  # already unicode
                        names.append(path)
                    fullnames.append(os.path.join(path, f))

        if verbose:
            print("> Found " + str(len(names)) + " files.")
        return fullnames, folders, names
