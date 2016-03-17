from symbtrdataextractor.SymbTrDataExtractor import SymbTrDataExtractor


class SymbTrAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._dataExtractor = SymbTrDataExtractor(print_warnings=verbose)

    def get_mbid_from_name(self):
        pass

    def extract_data_from_txt(self, txt_filename, symbtr_name=None, mbid=None,
                              segment_note_bound_idx=None):
        if self.verbose:
            print("- Extracting (meta)data from the SymbTr-txt file: " +
                  txt_filename)

        return self._dataExtractor.extract(
            txt_filename, symbtr_name=symbtr_name, mbid=mbid,
            segment_note_bound_idx=segment_note_bound_idx)

    def set_data_extractor_params(self, **kwargs):
        if any(key not in self._dataExtractor.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._dataExtractor.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._dataExtractor, key, value)
