import os


class SymbTrReader(object):
    @staticmethod
    def get_symbtr_name_from_filepath(score_file):
        return os.path.splitext(os.path.basename(score_file))[0]

    @staticmethod
    def is_symbtr_name(in_str):
        return len('--'.split(in_str)) == 5
