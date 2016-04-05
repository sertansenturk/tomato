import tempfile
import os
import pickle
from json_tricks import np as json


class IO(object):
    @staticmethod
    def create_temp_file(extension, contentstr):
        fd, temp_path = tempfile.mkstemp(extension)
        open_mode = 'wb' if extension in ['.mat'] else 'w'
        with open(temp_path, open_mode) as f:
            f.write(contentstr)
        os.close(fd)

        return temp_path

    @staticmethod
    def remove_temp_files(*argv):
        for path in argv:
            try:
                os.unlink(path)
            except OSError:  # directory
                os.rmdir(path)

    @staticmethod
    def load_json_from_temp_folder(temp_out_folder, expected):
        # load the results from the temporary folder
        out_dict = {}
        for exp in expected:
            fpath = os.path.join(temp_out_folder, exp + '.json')
            if os.path.isfile(fpath):
                out_dict[exp] = json.load(open(fpath, 'r'))
                os.unlink(fpath)  # remove file created in the temporary folder
            else:
                raise Exception(
                    'Missing output %s file' % exp)

        return out_dict

    @staticmethod
    def upper_key_first_letter(upper_dict):
        return IO._change_key_first_letter(upper_dict, "upper")

    @staticmethod
    def lower_key_first_letter(lower_dict):
        return IO._change_key_first_letter(lower_dict, "lower")

    @staticmethod
    def _change_key_first_letter(change_dict, operation):
        cdict = {}
        try:
            for k, v in change_dict.iteritems():
                cdict[getattr(k[:1], operation) + k[1:]] = \
                    IO._change_key_first_letter(v, operation)
        except AttributeError:  # input is not a dict, return
            cdict = change_dict

        return cdict

    @staticmethod
    def to_pickle(features, filepath=None):
        if filepath is None:
            return pickle.dumps(features)
        else:
            pickle.dump(features, open(filepath, 'wb'))

    @staticmethod
    def from_pickle(filepath):
        try:
            return pickle.load(open(filepath, 'rb'))
        except IOError:  # string given
            return pickle.loads(filepath)

    @staticmethod
    def to_json(features, filepath=None):
        if filepath is None:
            return json.dumps(features, indent=4)
        else:
            json.dump(features, open(filepath, 'w'), indent=4)

    @staticmethod
    def from_json(filepath):
        try:
            return json.load(open(filepath, 'r'))
        except IOError:  # string given
            return json.loads(filepath)
