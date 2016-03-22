from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor
from symbtrdataextractor.SymbTrDataExtractor import SymbTrReader


class SymbTrAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)
        self._symbTrReader = SymbTrReader()

    def get_mbid_from_name(self):
        pass

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

        return None

    def set_data_extractor_params(self, **kwargs):
        if any(key not in self._dataExtractor.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._dataExtractor.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._dataExtractor, key, value)
