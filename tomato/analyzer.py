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

from abc import ABCMeta, abstractmethod, abstractproperty
from io import IO
import logging
import warnings
from six import iteritems


class Analyzer(object):
    __metaclass__ = ABCMeta

    def __init__(self, verbose):
        self.verbose = verbose

    @abstractproperty
    def _inputs(self):
        pass

    @abstractmethod
    def analyze(self, *args, **kwargs):
        pass

    @abstractmethod
    def plot(self):
        pass

    def _set_params(self, analyzer_str, **kwargs):
        analyzer = getattr(self, analyzer_str)
        try:  # dictionary
            attribs = analyzer.keys()
        except AttributeError:  # object
            attribs = IO.public_noncallables(analyzer)

        Analyzer.chk_params(attribs, kwargs)

        for key, value in kwargs.items():
            try:  # dictionary
                analyzer[key] = value
            except TypeError:  # object
                setattr(analyzer, key, value)

    @staticmethod
    def chk_params(attribs, kwargs):
        if any(key not in attribs for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(attribs))

    def _parse_inputs(self, **kwargs):
        # initialize precomputed_features with the available analysis
        precomputed_features = dict((f, None)
                                    for f in self._inputs)
        for feature, val in iteritems(kwargs):
            if feature not in self._inputs:
                warn_str = u'Unrelated feature {0:s}: It will be kept, ' \
                           u'but it will not be used in the audio analysis.' \
                           u''.format(feature)
                warnings.warn(warn_str, stacklevel=2)
            precomputed_features[feature] = val

        return precomputed_features

    @staticmethod
    def _partial_caller(flag, func, *input_args, **input_kwargs):
        if flag is False:  # call skipped
            return None
        elif flag is None:  # call method
            try:
                return func(*input_args, **input_kwargs)
            except (RuntimeError, KeyError, IndexError, ValueError,
                    TypeError, AttributeError):
                logging.info('{0:s} failed.'.format(func.__name__))
                return None
        else:  # flag is the precomputed feature itself
            return flag

    @staticmethod
    def _get_first(feature):
        if isinstance(feature, list):  # list of features given
            return feature[0]  # for now get the first feature
        return feature

    def vprint(self, vstr):
        """
        Prints the input string if the verbose flag of the object is set to
        True
        :param vstr: input string to print
        """
        if self.verbose is True:
            print(vstr)

    def vprint_time(self, tic, toc):
        self.vprint(u"  The call took {0:.2f} seconds to execute.".
                    format(toc - tic))
