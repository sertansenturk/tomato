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

from .jointanalyzer import JointAnalyzer
from ..analyzer import Analyzer
from ..audio.audioanalyzer import AudioAnalyzer
from ..io import IO
from ..symbolic.symbtranalyzer import SymbTrAnalyzer


class CompleteAnalyzer(Analyzer):
    """
    Analyzer class, which does the complete audio analysis, score analysis and
    joint analysis.

    If you need to adjust parameters or if you need a faster, smarter,
    lightweight analysis, you should use the SymbTrAnalyzer, AudioAnalyzer and
    JointAnalyzer classes individually instead.
    """
    _inputs = []

    def __init__(self):
        """
        Initialize a CompleteAnalyzer object
        """
        super(CompleteAnalyzer, self).__init__(verbose=True)

        # extractors
        self._symbtr_analyzer = SymbTrAnalyzer(verbose=self.verbose)
        self._audio_analyzer = AudioAnalyzer(verbose=self.verbose)
        self._joint_analyzer = JointAnalyzer(verbose=self.verbose)

    def analyze(self, symbtr_txt_filename='', symbtr_mu2_filename='',
                symbtr_name=None, audio_filename='', audio_metadata=None):
        """
        Apply complete analysis of the input score(s) and audio recording

        Parameters
        ----------
        symbtr_txt_filename : str
            The SymbTr-score of the performed composition in txt format. It
            is used to parse the notated musical events and some editoral
            metadata
        symbtr_mu2_filename : str
            The SymbTr-score of the performed composition in mu2 format. It
            is used to parse additional editorial metadata and music theory
            information
        symbtr_name : str, optional
            The score name in the SymbTr convention, i.e.
            "makam--form--usul--name--composer." If not given the method
            will search the name in the symbtr_txt_filename
        audio_filename : str, optional
            The audio recording of the performed composition
        audio_metadata : str ot bool, optional
            The relevant recording MusicBrainz ID (MBID). IF not given, the
            method will try to fetch the MBID from tags in the recording. If
            the value is False, audio metadata will not be crawled
        Returns
        ----------
        dict
            The summary of the complete analysis from the features computed
            by the best available results.
        dict
            Features computed only using the music scores
        dict
            Features computed only using the audio recording
        dict
            Features related to audio recording, which are (re-)computed
            after audio-score alignment
        dict
            Features that are related to both the music scores and audio
            recordings.
        """
        symbtr_txt_filename = IO.make_unicode(symbtr_txt_filename)
        symbtr_mu2_filename = IO.make_unicode(symbtr_mu2_filename)
        audio_filename = IO.make_unicode(audio_filename)

        # score analysis
        score_features = self._symbtr_analyzer.analyze(
            symbtr_txt_filename, symbtr_mu2_filename, symbtr_name=symbtr_name)

        # audio analysis
        audio_features = self._audio_analyzer.analyze(
            audio_filename, makam=score_features['metadata']['makam']['symbtr_slug'],
            metadata=audio_metadata)

        # joint analysis
        joint_features, score_informed_audio_features = self._joint_analyzer.\
            analyze(symbtr_txt_filename, score_features, audio_filename,
                    audio_features['pitch'])

        # redo some steps in audio analysis
        score_informed_audio_features = self._audio_analyzer.analyze(
            metadata=False, pitch=False, **score_informed_audio_features)

        # summarize all the features extracted from all sources
        summarized_features = self._joint_analyzer.summarize(
            audio_features, score_features, joint_features,
            score_informed_audio_features)

        return (summarized_features, score_features, audio_features,
                score_informed_audio_features, joint_features)

    @staticmethod
    def plot(summarized_features):
        return JointAnalyzer.plot(summarized_features)
