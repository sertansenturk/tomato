import json
import os
import warnings

from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
from symbtrdataextractor.SymbTrDataExtractor import SymbTrReader
from symbtrextras.ScoreExtras import ScoreExtras
from musicbrainzngs import NetworkError

from tomato.MCRCaller import MCRCaller
from tomato.IO import IO
from tomato.ParamSetter import ParamSetter

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class SymbTrAnalyzer(ParamSetter):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)
        self._symbTrReader = SymbTrReader()
        self._phraseSegmenter = _mcr_caller.get_binary_path('phraseSeg')

    def analyze(self, txt_filepath, mu2_filepath, symbtr_name=None):
        # attempt to get the symbtrname from the filename, if it is not given
        if symbtr_name is None:
            symbtr_name = os.path.splitext(os.path.basename(txt_filepath))[0]

        # Automatic phrase segmentation on the SymbTr-txt score
        try:
            boundary_note_idx = self.segment_phrase(
                txt_filepath, symbtr_name=symbtr_name)['boundary_note_idx']
        except IOError as e:
            boundary_note_idx = None
            if self.verbose:
                warnings.warn(e.message, RuntimeWarning)

        # relevant recording or work mbid
        mbid = ScoreExtras.get_mbids(symbtr_name)
        if not mbid and self.verbose:
            warnings.warn("No MBID returned for %s" % symbtr_name,
                          RuntimeWarning)
        else:
            # Note: very rare but there can be more that one mbid returned.
            #       We are going to use the first work to fetch the metadata
            mbid = mbid[0]

        # Extract the (meta)data from the SymbTr scores
        try:
            score_data, is_data_valid = self.extract_data(
                txt_filepath, mu2_filepath, symbtr_name=symbtr_name, mbid=mbid,
                segment_note_bound_idx=boundary_note_idx)
        except NetworkError:  # musicbrainz is not available
            if self.verbose:
                warnings.warn('Unable to reach http://musicbrainz.org/. '
                              'The metadata stored there is not available.',
                              RuntimeWarning)
            score_data, is_data_valid = self.extract_data(
                txt_filepath, mu2_filepath, symbtr_name=symbtr_name,
                segment_note_bound_idx=boundary_note_idx)

        if not is_data_valid and self.verbose:
            warnings.warn(symbtr_name + ' has validation problems.')

        return score_data

    def segment_phrase(self, txt_filename, symbtr_name=None):
        if self.verbose:
            print("- Automatic phrase segmentation on the SymbTr-txt file: " +
                  txt_filename)

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
        callstr = ["%s segmentWrapper %s %s %s %s" %
                   (self._phraseSegmenter, bound_stat_file, fld_model_file,
                    temp_in_file, temp_out_file)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output,
        # The prints are in segmentWrapper function in the MATLAB code
        if "segmentation complete!" not in out:
            IO.remove_temp_files(temp_in_file, temp_out_file)
            raise IOError("Phrase segmentation is not successful. Please "
                          "check and report the error in the terminal.")

        # load the results from the temporary file
        phrase_boundaries = json.load(open(temp_out_file))

        # unlink the temporary files
        IO.remove_temp_files(temp_in_file, temp_out_file)

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
        if self.verbose:
            print("- Extracting (meta)data from the SymbTr-txt file: " +
                  txt_filename)

        txt_data, is_txt_valid = self._dataExtractor.extract(
            txt_filename, symbtr_name=symbtr_name, mbid=mbid,
            segment_note_bound_idx=segment_note_bound_idx)

        if self.verbose:
            print("- Extracting metadata from the SymbTr-mu2 file: " +
                  mu2_filename)

        mu2_header, header_row, is_mu2_header_valid = \
            self._symbTrReader.read_mu2_header(
                mu2_filename, symbtr_name=symbtr_name)

        data = SymbTrDataExtractor.merge(txt_data, mu2_header)
        is_data_valid = {'is_all_valid': (is_mu2_header_valid and
                                          is_txt_valid),
                         'is_txt_valid': is_txt_valid,
                         'is_mu2_header_valid': is_mu2_header_valid}

        return data, is_data_valid

    def set_data_extractor_params(self, **kwargs):
        self._set_params('_dataExtractor', **kwargs)
