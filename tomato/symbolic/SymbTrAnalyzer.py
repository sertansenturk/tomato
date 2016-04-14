import json
import os
import warnings
import timeit

from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
from symbtrdataextractor.reader.Mu2Reader import Mu2Reader
from symbtrextras.ScoreExtras import ScoreExtras
from musicbrainzngs import NetworkError
from musicbrainzngs import ResponseError

from ..MCRCaller import MCRCaller
from ..IO import IO
from ..Analyzer import Analyzer

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class SymbTrAnalyzer(Analyzer):
    _inputs = ['boundaries', 'mbid', 'score_features']

    def __init__(self, verbose=False):
        super(SymbTrAnalyzer, self).__init__(verbose=verbose)

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)
        self._mu2Reader = Mu2Reader()
        self._phraseSegmenter = _mcr_caller.get_binary_path('phraseSeg')

    def analyze(self, txt_filepath, mu2_filepath, symbtr_name=None, **kwargs):
        input_f = self._parse_inputs(**kwargs)

        # attempt to get the symbtr_name from the filename, if it is not given
        if symbtr_name is None:
            symbtr_name = os.path.splitext(os.path.basename(txt_filepath))[0]

        # Automatic phrase segmentation on the SymbTr-txt score
        input_f['boundaries'] = self._partial_caller(
            input_f['boundaries'], self.segment_phrase, txt_filepath,
            symbtr_name=symbtr_name)

        # get relevant recording or work mbid
        # Note: very rare but there can be more that one mbid returned.
        #       We are going to use the first mbid to fetch the metadata
        # TODO: use all mbids
        input_f['mbid'] = self._partial_caller(input_f['mbid'], self.get_mbids,
                                               symbtr_name)
        input_f['mbid'] = self._get_first(input_f['mbid'])

        # Extract the (meta)data from the SymbTr scores. Here the results from
        # the previous steps are also summarized.
        self._partial_call_extract_data(input_f, txt_filepath, mu2_filepath,
                                        symbtr_name)

        return (input_f['score_features'], input_f['boundaries'],
                input_f['mbid'])

    def _partial_call_extract_data(self, features, txt_filepath, mu2_filepath,
                                   symbtr_name):
        # If MusicBrainz is not available, crawling will be skipped by the
        # makammusicbrainz package
        score_data = self._partial_caller(
            features['score_features'], self.extract_data, txt_filepath,
            mu2_filepath, symbtr_name=symbtr_name, mbid=features['mbid'],
            segment_note_bound_idx=features['boundaries'][
                'boundary_note_idx'])

        # validate
        if score_data is not None:
            score_features, is_valid = score_data
            if not is_valid:
                warnings.warn(symbtr_name + ' has validation problems.')
        else:
            score_features, is_valid = [None, None]

        features['score_features'] = score_features

    @staticmethod
    def get_mbids(symbtr_name):
        mbids = ScoreExtras.get_mbids(symbtr_name)
        if not mbids:
            warnings.warn(u"No MBID returned for {0:s}".format(symbtr_name),
                          RuntimeWarning)
        return mbids

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
        call_str = ["{0:s} segmentWrapper {1:s} {2:s} {3:s} {4:s}".format(
            self._phraseSegmenter, bound_stat_file, fld_model_file,
            temp_in_file, temp_out_file)]

        out, err = _mcr_caller.call(call_str)

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

    def extract_data(self, txt_filename, mu2_filename, symbtr_name=None,
                     mbid=None, segment_note_bound_idx=None):

        # SymbTr-txt file
        tic = timeit.default_timer()
        self.vprint(u"- Extracting (meta)data from the SymbTr-txt file: {0:s}"
                    .format(txt_filename))

        txt_data, is_txt_valid = self._dataExtractor.extract(
            txt_filename, symbtr_name=symbtr_name, mbid=mbid,
            segment_note_bound_idx=segment_note_bound_idx)

        # print elapsed time, if verbose
        self.vprint_time(tic, timeit.default_timer())

        # SymbTr-txt file
        tic2 = timeit.default_timer()
        self.vprint(u"- Extracting metadata from the SymbTr-mu2 file: {0:s}"
                    .format(mu2_filename))

        mu2_header, header_row, is_mu2_header_valid = \
            self._mu2Reader.read_header(
                mu2_filename, symbtr_name=symbtr_name)

        score_features = SymbTrDataExtractor.merge(txt_data, mu2_header)
        is_data_valid = {'is_all_valid': (is_mu2_header_valid and
                                          is_txt_valid),
                         'is_txt_valid': is_txt_valid,
                         'is_mu2_header_valid': is_mu2_header_valid}

        # print elapsed time, if verbose
        self.vprint_time(tic2, timeit.default_timer())

        return score_features, is_data_valid

    # plot
    @staticmethod
    def plot(score_features):
        return NotImplemented

    # setters
    def set_data_extractor_params(self, **kwargs):
        self._set_params('_dataExtractor', **kwargs)
