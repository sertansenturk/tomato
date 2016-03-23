from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
from symbtrdataextractor.SymbTrDataExtractor import SymbTrReader
from .. _binaries.MCRCaller import MCRCaller
import os
import subprocess
import tempfile
import json

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class SymbTrAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)
        self._symbTrReader = SymbTrReader()
        self._phraseSegmenter = self._get_phrase_segmenter_path()

    @staticmethod
    def _get_phrase_segmenter_path():
        if _mcr_caller.sys_os == 'linux':
            phrase_seg_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..',
                '_binaries', 'phraseSeg')
        elif _mcr_caller.sys_os == 'macosx':
            phrase_seg_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), '..',
                '_binaries', 'phraseSeg.app', 'Contents', 'MacOS', 'phraseSeg')
        else:
            raise ValueError('Unsupported OS.')

        return phrase_seg_path

    def segment_phrase(self, txt_filename, symbtr_name=None):
        if self.verbose:
            print("- Automatic phrase segmentation on the SymbTr-txt file: " +
                  txt_filename)

        # attempt to get the symbtrname from the filename, if it is not given
        if symbtr_name is None:
            symbtr_name = os.path.basename(txt_filename)

        # create the temporary input and output files wanted by the binary
        temp_in_file = self._create_temp_file(
            '.json', json.dumps([{'path': txt_filename, 'name': symbtr_name}]))
        temp_out_file = self._create_temp_file('.json', '')

        # get the pretrained model
        bound_stat_file, fld_model_file = self._get_phrase_seg_training()

        # call the binary
        proc = subprocess.Popen(
            ["%s segmentWrapper %s %s %s %s" %
             (self._phraseSegmenter, bound_stat_file, fld_model_file,
              temp_in_file, temp_out_file)],
            stdout=subprocess.PIPE, shell=True, env=_mcr_caller.env)

        (out, err) = proc.communicate()

        # load the results from the temporary file
        phrase_boundaries = json.load(open(temp_out_file))

        # unlink the temporary files
        os.unlink(temp_in_file)
        os.unlink(temp_out_file)

        # check the MATLAB output,
        # The prints are in segmentWrapper function in the MATLAB code
        if "segmentation complete!" not in out:
            raise IOError("The phrase segmentation is unsuccessful. Please "
                          "check/report the error in the terminal.")

        return phrase_boundaries

    @staticmethod
    def _create_temp_file(extension, contentstr):
        fd, temp_path = tempfile.mkstemp(extension)
        with open(temp_path, 'w') as f:
            f.write(contentstr)
        os.close(fd)

        return temp_path

    @staticmethod
    def _get_phrase_seg_training():
        bound_stat_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '_models', 'phrase_segmentation', 'boundStat.mat')
        fld_model_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '_models', 'phrase_segmentation', 'FLDModel.mat')

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
        is_data_valid = {'results': is_mu2_header_valid and is_txt_valid,
                         'is_txt_valid': is_txt_valid,
                         'is_mu2_header_valid': is_mu2_header_valid}

        return data, is_data_valid

    def set_data_extractor_params(self, **kwargs):
        if any(key not in self._dataExtractor.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._dataExtractor.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._dataExtractor, key, value)
