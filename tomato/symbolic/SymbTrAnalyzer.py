from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
from symbtrdataextractor.SymbTrDataExtractor import SymbTrReader
from .. _binaries.MCRCaller import MCRCaller
import os
import subprocess
import tempfile

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class SymbTrAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)
        self._symbTrReader = SymbTrReader()
        self._phraseSegmentor = self._get_phrase_segmentor_path()

    def get_mbid_from_name(self):
        pass

    @staticmethod
    def _get_phrase_segmentor_path():
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

    def segment_phrase(self, txt_filename):
        if self.verbose:
            print("- Automatic phrase segmentation on the SymbTr-txt file: " +
                  txt_filename)

        bound_stat_file, fld_model_file = self._get_phrase_seg_training()

        # proc = subprocess.Popen(["/srv/dunya/phraseSeg segmentWrapper %s
        # %s %s %s" % (boundstat, fldmodel, files_json, out_json)],
        # stdout=subprocess.PIPE, shell=True, env=subprocess_env)
        proc = subprocess.Popen(["%s unitTest" % (self._phraseSegmentor)],stdout=subprocess.PIPE, shell=True,env=_mcr_caller.env)

        (out, err) = proc.communicate()

        return None

    @staticmethod
    def _get_phrase_seg_training():
        bound_stat_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '_models', 'phrase_segmentation', 'boundStat.mat')
        fld_model_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '_models', 'phrase_segmentation', 'FLDModel.mat')

        return bound_stat_file, fld_model_file

    def set_data_extractor_params(self, **kwargs):
        if any(key not in self._dataExtractor.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._dataExtractor.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._dataExtractor, key, value)
