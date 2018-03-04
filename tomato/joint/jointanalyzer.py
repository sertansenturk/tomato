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

import json
import tempfile
from copy import deepcopy
import timeit
import warnings
import logging
from scipy.io import savemat
from six import BytesIO

from .alignedpitchfilter import AlignedPitchFilter
from .alignednotemodel import AlignedNoteModel

from ..bincaller import BinCaller
from ..io import IO
from ..analyzer import Analyzer
from ..plotter import Plotter

logger = logging.Logger(__name__, level=logging.INFO)

# instantiate a mcr_caller
_mcr_caller = BinCaller()


class JointAnalyzer(Analyzer):
    _inputs = ['notes', 'note_models', 'makam', 'pitch_filtered', 'sections',
               'tonic', 'tempo']

    def __init__(self, verbose=False):
        super(JointAnalyzer, self).__init__(verbose=verbose)

        # extractors
        self._tonic_tempo_extractor = _mcr_caller.get_mcr_binary_path(
            'extractTonicTempoTuning')
        self._audio_score_aligner = _mcr_caller.get_mcr_binary_path(
            'alignAudioScore')
        self._aligned_pitch_filter = AlignedPitchFilter()
        self._aligned_note_model = AlignedNoteModel()

    def analyze(self, symbtr_txt_filename='', score_features=None,
                audio_filename='', audio_pitch=None, **kwargs):
        input_f = self._parse_inputs(**kwargs)
        audio_filename = IO.make_unicode(audio_filename)
        symbtr_txt_filename = IO.make_unicode(symbtr_txt_filename)

        # joint score-informed tonic identification and tempo estimation
        try:  # if both are given in advance don't recompute
            input_f['tonic'], input_f['tempo'] = self.extract_tonic_tempo(
                symbtr_txt_filename, score_features, audio_filename,
                audio_pitch)
        except RuntimeError as e:
            warnings.warn(e.message, RuntimeWarning, stacklevel=2)
            joint_features = None
            score_informed_audio_features = {
                'makam': score_features['makam']['symbtr_slug']}
            # Everything else will fail
            return joint_features, score_informed_audio_features

        # section linking and note-level alignment
        try:
            temp_out = self.align_audio_score(
                symbtr_txt_filename, score_features, audio_filename,
                audio_pitch, input_f['tonic'], input_f['tempo'])
            input_f['aligned_sections'], input_f['notes'], input_f[
                'section_links'], input_f['section_candidates'] = temp_out
        except RuntimeError as e:
            warnings.warn(e.message, RuntimeWarning, stacklevel=2)
            joint_features = None
            score_informed_audio_features = {
                'tonic': input_f['tonic'], 'tempo': input_f['tempo'],
                'makam': score_features['makam']['symbtr_slug']}
            return joint_features, score_informed_audio_features

        # aligned pitch filter
        temp_out = self._partial_caller(
            input_f['pitch_filtered'], self.filter_pitch, audio_pitch,
            input_f['notes'])
        if temp_out is not None:
            input_f['pitch_filtered'], input_f['notes'] = temp_out
        else:
            input_f['pitch_filtered'], input_f['notes'] = [None, None]

        # aligned note models
        temp_out = self._partial_caller(
            input_f['note_models'], self.compute_note_models,
            input_f['pitch_filtered'], input_f['notes'],
            input_f['tonic']['symbol'])
        if temp_out is not None:
            input_f['note_models'], dummy_pd, input_f['tonic'] = temp_out
        else:
            input_f['note_models'], input_f['tonic'] = [None, None]

        joint_features = {'sections': input_f['aligned_sections'],
                          'notes': input_f['notes']}

        score_informed_audio_features = {
            'makam': score_features['makam']['symbtr_slug'],
            'pitch_filtered': input_f['pitch_filtered'],
            'tonic': input_f['tonic'], 'tempo': input_f['tempo'],
            'note_models': input_f['note_models']}

        return joint_features, score_informed_audio_features

    @classmethod
    def summarize(cls, audio_features=None, score_features=None,
                  joint_features=None, score_informed_audio_features=None):
        # initialize the summary dict
        sdict = {'score': score_features, 'audio': {}, 'joint': {}}

        sdict['audio'] = cls._summarize_common_audio_features(
            audio_features, score_informed_audio_features)

        # pitch_filtered is a redundant name and it might not have been
        # computed
        sdict['audio']['pitch'] = sdict['audio'].pop("pitch_filtered", None)
        if sdict['audio']['pitch'] is None and audio_features:
            sdict['audio']['pitch'] = audio_features.get('pitch')

        # tempo if computed
        try:
            sdict['audio']['tempo'] = score_informed_audio_features['tempo']
        except KeyError:
            logger.debug("Tempo feature is not available.")

        # accumulate joint dict
        try:
            sdict['joint']['sections'] = joint_features['sections']
            sdict['joint']['notes'] = joint_features['notes']
        except (KeyError, TypeError):
            sdict['joint'] = {}
            logger.debug("Section links and aligned notes are not available.")

        return sdict

    @staticmethod
    def _summarize_common_audio_features(audio_features,
                                         score_informed_audio_features):
        common_feature_names = ['makam', 'melodic_progression', 'note_models',
                                'pitch_class_distribution',
                                'pitch_distribution', 'pitch_filtered',
                                'tonic', 'transposition']

        common_audio_features = dict()
        for cf in common_feature_names:
            if score_informed_audio_features:
                common_audio_features[cf] = \
                    score_informed_audio_features.get(cf)

            if not common_audio_features.get(cf):
                if audio_features:
                    common_audio_features[cf] = audio_features.get(cf)
                else:
                    common_audio_features[cf] = None

        return common_audio_features

    def extract_tonic_tempo(self, score_filename='', score_data=None,
                            audio_filename='', audio_pitch=None):
        tic = timeit.default_timer()
        score_filename = IO.make_unicode(score_filename)
        audio_filename = IO.make_unicode(audio_filename)
        self.vprint(u"- Extracting score-informed tonic and tempo of {0:s}"
                    .format(audio_filename))

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = IO.create_temp_file(
            '.json', json.dumps(score_data))

        # matlab
        matout = BytesIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = IO.create_temp_file(
            '.mat', matout.getvalue())

        temp_out_folder = tempfile.mkdtemp()

        # call the binary
        callstr = [u'"{0:s}" "{1:s}" "{2:s}" "{3:s}" "{4:s}" "{5:s}"'.format(
            self._tonic_tempo_extractor, score_filename, temp_score_data_file,
            audio_filename, temp_pitch_file, temp_out_folder)]
        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        if "Tonic-Tempo-Tuning Extraction took" not in out.decode('utf-8'):
            IO.remove_temp_files(
                temp_score_data_file, temp_pitch_file, temp_out_folder)
            raise RuntimeError("Score-informed tonic, tonic and tuning "
                               "extraction is not successful. Please "
                               "check the error in the terminal.")

        out_dict = IO.load_json_from_temp_folder(
            temp_out_folder, ['tempo', 'tonic', 'tuning'])

        # unlink the temporary files
        IO.remove_temp_files(
            temp_score_data_file, temp_pitch_file, temp_out_folder)

        # tidy outouts
        # We omit the tuning output in the binary because
        # get_aligned_note_models is more informative
        procedure = 'Score informed joint tonic and tempo extraction'

        tonic = out_dict['tonic']['scoreInformed']
        tonic = IO.dict_keys_to_snake_case(tonic)
        tonic['procedure'] = procedure
        tonic['source'] = audio_filename

        tempo = out_dict['tempo']['scoreInformed']
        tempo['average'] = IO.dict_keys_to_snake_case(tempo['average'])
        tempo['average']['procedure'] = procedure
        tempo['average']['source'] = audio_filename
        tempo['average'].pop("method", None)

        tempo['relative'] = IO.dict_keys_to_snake_case(
            tempo['relative'])
        tempo['relative']['procedure'] = procedure
        tempo['relative']['source'] = audio_filename
        tempo['relative'].pop("method", None)

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())

        return tonic, tempo

    def align_audio_score(self, score_filename='', score_data=None,
                          audio_filename='', audio_pitch=None,
                          audio_tonic=None, audio_tempo=None):
        tic = timeit.default_timer()
        score_filename = IO.make_unicode(score_filename)
        audio_filename = IO.make_unicode(audio_filename)
        self.vprint(u"- Aligning audio recording {0:s} and music score {1:s}."
                    .format(audio_filename, score_filename))

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = IO.create_temp_file(
            '.json', json.dumps(score_data))

        # tonic has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tonic_ = IO.dict_keys_to_camel_case(audio_tonic)
        temp_tonic_file = IO.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tonic_}))

        # tempo has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tempo_ = deepcopy(audio_tempo)
        audio_tempo_['relative'] = IO.dict_keys_to_camel_case(
            audio_tempo['relative'])
        audio_tempo_['average'] = IO.dict_keys_to_camel_case(
            audio_tempo['average'])
        temp_tempo_file = IO.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tempo_}))

        # matlab
        matout = BytesIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = IO.create_temp_file(
            '.mat', matout.getvalue())

        temp_out_folder = tempfile.mkdtemp()

        # call the binary
        callstr = [u'"{0:s}" "{1:s}" "{2:s}" "" "{3:s}" "{4:s}" "{5:s}" '
                   u'"{6:s}" "" "{7:s}"'
                   u''.format(self._audio_score_aligner, score_filename,
                              temp_score_data_file, audio_filename,
                              temp_pitch_file, temp_tonic_file,
                              temp_tempo_file, temp_out_folder)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        if "Audio-score alignment took" not in out.decode('utf-8'):
            IO.remove_temp_files(
                temp_score_data_file, temp_tonic_file, temp_tempo_file,
                temp_pitch_file, temp_out_folder)
            raise RuntimeError("Audio score alignment is not successful. "
                               "Please check the error in the terminal.")

        out_dict = IO.load_json_from_temp_folder(
            temp_out_folder, ['sectionLinks', 'alignedNotes'])

        # unlink the temporary files
        IO.remove_temp_files(temp_score_data_file, temp_tonic_file,
                             temp_tempo_file, temp_pitch_file, temp_out_folder)

        notes = [IO.dict_keys_to_snake_case(n)
                 for n in out_dict['alignedNotes']['notes']]

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())

        return (out_dict['sectionLinks']['alignedLinks'], notes,
                out_dict['sectionLinks']['sectionLinks'],
                out_dict['sectionLinks']['candidateLinks'])

    def filter_pitch(self, pitch, aligned_notes):
        tic = timeit.default_timer()
        self.vprint(u"- Filtering predominant melody of {0:s} after "
                    u"audio-score alignment.".format(pitch['source']))
        aligned_notes_ = [IO.dict_keys_to_camel_case(n)
                          for n in deepcopy(aligned_notes)]

        pitch_temp, notes_filtered, synth_pitch = \
            self._aligned_pitch_filter.filter(pitch['pitch'], aligned_notes_)

        notes_filtered = [IO.dict_keys_to_snake_case(n)
                          for n in notes_filtered]

        pitch_filtered = deepcopy(pitch)
        pitch_filtered['pitch'] = pitch_temp
        pitch_filtered['citation'] = 'SenturkThesis'
        pitch_filtered['procedure'] = 'Pitch filtering according to ' \
                                      'audio-score alignment'

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())

        return pitch_filtered, notes_filtered

    def compute_note_models(self, pitch, aligned_notes, tonic_symbol):
        tic = timeit.default_timer()
        self.vprint(u"- Computing the note models for {0:s}".
                    format(pitch['source']))

        aligned_notes_ = [IO.dict_keys_to_camel_case(n)
                          for n in deepcopy(aligned_notes)]

        note_models, pitch_distribution, tonic = self._aligned_note_model.\
            get_models(pitch['pitch'], aligned_notes_, tonic_symbol)

        for note in note_models.keys():
            note_models[note] = IO.dict_keys_to_snake_case(
                note_models[note])

        tonic = IO.dict_keys_to_snake_case(tonic['alignment'])
        tonic['source'] = pitch['source']

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())
        return note_models, pitch_distribution, tonic

    def set_tonic_tempo_extractor_params(self, **kwargs):
        raise NotImplementedError

    def set_audio_score_aligner_params(self, **kwargs):
        raise NotImplementedError

    def set_pitch_filter_params(self, **kwargs):
        self._set_params('_aligned_pitch_filter', **kwargs)

    def set_note_model_params(self, **kwargs):
        self._set_params('_aligned_note_model', **kwargs)

    @staticmethod
    def plot(summarized_features):
        # audio features
        pitch = summarized_features['audio']['pitch']['pitch']
        pitch_distribution = summarized_features['audio']['pitch_distribution']
        melodic_progression = summarized_features['audio'][
            'melodic_progression']
        note_models = summarized_features['audio']['note_models']
        makam = summarized_features['score']['makam']
        tonic = summarized_features['audio']['tonic']
        transposition = summarized_features['audio']['transposition']
        tempo = summarized_features['audio']['tempo']

        # joint features
        try:
            sections = summarized_features['joint']['sections']
        except KeyError:  # section linking failed
            sections = None
        try:
            aligned_notes = summarized_features['joint']['notes']
        except KeyError:  # audio score alignment failed
            aligned_notes = None

        return Plotter.plot_audio_features(
            pitch=pitch, pitch_distribution=pitch_distribution,
            sections=sections, notes=aligned_notes, note_models=note_models,
            melodic_progression=melodic_progression, makam=makam, tonic=tonic,
            transposition=transposition, tempo=tempo)
