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

from six.moves import configparser
import os
import subprocess

from io import IO


class BinCaller(object):
    def __init__(self):
        self.mcr_filepath = IO.get_abspath_from_relpath_in_tomato(
            'config', 'mcr_path.cfg')

        self.env, self.sys_os = self.set_environment()

    def set_environment(self):
        config = configparser.SafeConfigParser()
        config.read(self.mcr_filepath)
        try:
            op_sys, env_var, mcr_path, set_paths = \
                self._get_mcr_config(config, 'custom')
        except (IOError, ValueError):
            try:
                op_sys, env_var, mcr_path, set_paths = \
                    self._get_mcr_config(config, 'linux_default')
            except (IOError, ValueError):
                op_sys, env_var, mcr_path, set_paths = \
                    self._get_mcr_config(config, 'macosx_default')

        subprocess_env = os.environ.copy()
        subprocess_env["MCR_CACHE_ROOT"] = "/tmp/emptydir"
        subprocess_env["LANG"] = "en_US.utf8"
        subprocess_env[env_var] = set_paths

        return subprocess_env, op_sys

    def call(self, callstr):
        proc = subprocess.Popen(callstr, stdout=subprocess.PIPE, shell=True,
                                env=self.env)
        return proc.communicate()

    @staticmethod
    def _get_mcr_config(config, section_str):
        op_sys = config.get(section_str, 'sys_os')
        env_var = config.get(section_str, 'env_var')
        mcr_path = config.get(section_str, 'mcr_path')
        set_paths = config.get(section_str, 'set_paths')

        # MCR installation path is not found
        if not os.path.exists(mcr_path):
            raise IOError('The mcr path is not found. Please '
                          'fill the custom section in '
                          '"tomato/config/mcr_path.cfg" manually.')

        # The configuration is wrong
        if not bool(env_var):
            raise ValueError('One of the fields for the MCR '
                             'path is empty in "tomato/config/mcr_path.cfg". '
                             'Please reconfigure manually.')

        return op_sys, env_var, mcr_path, set_paths

    def get_mcr_binary_path(self, bin_name):
        if self.sys_os == 'linux':
            bin_path = IO.get_abspath_from_relpath_in_tomato(
                'bin', bin_name)
        elif self.sys_os == 'macosx':
            bin_path = IO.get_abspath_from_relpath_in_tomato(
                'bin', bin_name + '.app', 'Contents', 'MacOS', bin_name)
        else:
            raise ValueError('Unsupported OS.')

        self.check_bin_exists(bin_path)

        return bin_path

    def get_musikitomusicxml_binary_path(self):
        if self.sys_os in ['linux', 'macosx']:
            bin_path = IO.get_abspath_from_relpath_in_tomato(
                'bin', 'MusikiToMusicXml')
        else:
            raise ValueError('Unsupported OS.')

        self.check_bin_exists(bin_path)

        return bin_path

    def get_lilypond_bin_path(self):
        config = configparser.SafeConfigParser()
        lily_cfgfile = IO.get_abspath_from_relpath_in_tomato(
            'config', 'lilypond.cfg')
        config.read(lily_cfgfile)

        # check custom
        lilypath = config.get('custom', 'custom')

        # linux path might be given with $HOME; convert it to the real path
        lilypath = lilypath.replace('$HOME', os.path.expanduser('~'))

        if lilypath:
            assert os.path.exists(lilypath), \
                'The lilypond path is not found. Please correct the custom ' \
                'section in "tomato/config/lilypond.cfg".'
        else:  # defaults
            lilypath = config.defaults()[self.sys_os]

            assert (os.path.exists(lilypath) or
                    self.call('"which" "{0:s}"'.format(lilypath))[0]), \
                'The lilypond path is not found. Please correct the custom ' \
                'section in "tomato/config/lilypond.cfg".'

        return lilypath

    @staticmethod
    def check_bin_exists(bin_path):
        assert os.path.exists(bin_path), u'Binary does not exist: {0:s}'.\
            format(bin_path)
