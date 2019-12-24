
# Copyright 2016 - 2018 Sertan Şentürk
#
# This file is part of tomato: https://github.com/sertansenturk/tomato/
#
# tomato is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation (FSF), either version 3 of the License,
# or (at your option) any later version.
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
import os
import timeit

from ..analyzer import Analyzer
from ..bincaller import BinCaller
from ..io import IO
from ..metadata.symbtr import SymbTr as SymbTrMetadata
from .symbtr.dataextractor import DataExtractor
from .symbtr.reader.mu2 import Mu2Reader
from .symbtr.reader.txt import TxtReader
from .symbtr.rhythmicfeature import RhythmicFeatureExtractor
from .symbtr.section import SectionExtractor
from .symbtr.segment import SegmentExtractor

# instantiate a mcr_caller
_mcr_caller = BinCaller()


class SymbTrAnalyzer(Analyzer):
    _inputs = ['mbid', 'metadata', 'sections', 'phrase_annotations',
               'segment_boundaries', 'segments', 'rhythmic_structure',
               'score', 'is_data_valid']

    def __init__(self, verbose=False):
        super(SymbTrAnalyzer, self).__init__(verbose=verbose)

        # extractors
        self._data_extractor = DataExtractor(print_warnings=verbose)
        self._phrase_segmenter = _mcr_caller.get_mcr_binary_path('phraseSeg')
        self._section_extractor = SectionExtractor()
        self._segment_extractor = SegmentExtractor()

    def analyze(self, txt_filepath, mu2_filepath=None, symbtr_name=None,
                **kwargs):
        score_data = self._parse_inputs(**kwargs)

        # attempt to get the symbtr_name from the filename, if it is not given
        if symbtr_name is None:
            symbtr_name = os.path.splitext(os.path.basename(txt_filepath))[0]

        # get relevant recording or work mbid
        # Note: very rare but there can be more that one mbid returned.
        #       We are going to use the first mbid to fetch the symbtr
        # TODO: use all mbids
        score_data['mbid'] = self._partial_caller(
            score_data['mbid'], SymbTrMetadata.get_mbids_from_symbtr_name,
            symbtr_name)
        score_data['mbid'] = self._partial_caller(
            None, self._get_first, score_data['mbid'])

        # read the txt score
        score_data['score'], is_score_content_valid = TxtReader.read(
            txt_filepath, symbtr_name=symbtr_name)

        # get the symbtr metadata
        score_data['metadata'], is_metadata_valid = self._partial_caller(
            score_data['metadata'], SymbTrMetadata.from_musicbrainz,
            symbtr_name, mbid=score_data['mbid'])

        score_data['metadata']['duration'] = {
            'value': sum(score_data['score']['duration']) * 0.001,
            'unit': 'second'}
        score_data['metadata']['number_of_notes'] = len(
            score_data['score']['duration'])

        if mu2_filepath is not None:
            mu2_header, header_row, is_mu2_header_valid = \
                Mu2Reader.read_header(mu2_filepath, symbtr_name=symbtr_name)

            score_data['metadata'] = DataExtractor.merge(
                score_data['metadata'], mu2_header)

        # sections
        score_data['sections'], is_section_data_valid = \
            self._section_extractor.from_txt_score(
                score_data['score'], symbtr_name)

        # annotated phrases
        anno_phrases = self._segment_extractor.extract_phrases(
            score_data['score'], sections=score_data['sections'])
        score_data['phrase_annotations'] = anno_phrases

        # Automatic phrase segmentation on the SymbTr-txt score
        score_data['segment_boundaries'] = self._partial_caller(
            score_data['segment_boundaries'], self.segment_phrase,
            txt_filepath, symbtr_name=symbtr_name)
        if score_data['segment_boundaries'] is None:
            score_data['segment_boundaries'] = {'boundary_beat': None,
                                                'boundary_note_idx': None}

        score_data['segments'] = self._segment_extractor.extract_segments(
            score_data['score'],
            score_data['segment_boundaries']['boundary_note_idx'],
            sections=score_data['sections'])

        # rhythmic structure
        score_data['rhythmic_structure'] = \
            RhythmicFeatureExtractor.extract_rhythmic_structure(
                score_data['score'])

        score_data['is_data_valid'] = all(
            [is_metadata_valid, is_section_data_valid, is_score_content_valid])

        return score_data

    def segment_phrase(self, txt_filename, symbtr_name=None):
        tic = timeit.default_timer()
        self.vprint(u"- Automatic phrase segmentation on the SymbTr-txt file: "
                    u"{0:s}".format(txt_filename))

        # attempt to get the symbtrname from the filename, if it is not given
        if symbtr_name is None:
            symbtr_name = os.path.basename(txt_filename)

        # create the temporary input and output files wanted by the binary
        temp_in_file = IO.create_temp_file(
            '.json', json.dumps([{'path': txt_filename, 'name': symbtr_name}]))
        temp_out_file = IO.create_temp_file('.json', '')

        # get the pretrained model
        bound_stat_file, fld_model_file = self._get_phrase_seg_training()

        # call the binary
        callstr = [u'"{0:s}" "segmentWrapper" "{1:s}" "{2:s}" "{3:s}" "{4:s}"'
                   u''.format(self._phrase_segmenter, bound_stat_file,
                              fld_model_file, temp_in_file, temp_out_file)]

        out, err = _mcr_caller.call(callstr)
        out = out.decode("utf-8")  # convert from byte to urf-8 str

        # check the MATLAB output,
        # The prints are in segmentWrapper function in the MATLAB code
        if "segmentation complete!" not in out:
            IO.remove_temp_files(temp_in_file, temp_out_file)
            raise RuntimeError("Phrase segmentation is not successful. Please "
                               "check the error in the terminal.")

        # load the results from the temporary file
        phrase_boundaries = json.load(open(temp_out_file))

        # unlink the temporary files
        IO.remove_temp_files(temp_in_file, temp_out_file)

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())

        return phrase_boundaries

    @staticmethod
    def _get_phrase_seg_training():
        phrase_seg_training_path = IO.get_abspath_from_relpath_in_tomato(
            'models', 'phrase_segmentation')
        bound_stat_file = os.path.join(
            phrase_seg_training_path, 'boundStat.mat')
        fld_model_file = os.path.join(
            phrase_seg_training_path, 'FLDmodel.mat')

        return bound_stat_file, fld_model_file

    # plot
    @staticmethod
    def plot(score_features):
        return NotImplemented

    # setters
    def set_data_extractor_params(self, **kwargs):
        self._set_params('_data_extractor', **kwargs)

    # setters
    def set_section_extractor_params(self, **kwargs):
        self._set_params('_section_extractor', **kwargs)

    def set_segment_extractor_params(self, **kwargs):
        self._set_params('_segment_extractor', **kwargs)
