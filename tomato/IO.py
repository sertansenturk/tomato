import tempfile
import os
from json_tricks import np as json
import pickle
import re


class IO(object):
    @staticmethod
    def get_abspath_from_relpath_in_tomato(*args):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

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
                raise Exception('Missing output %s file' % exp)

        return out_dict

    # compiled regular expressions for dict_keys_to_snake_case
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @staticmethod
    def dict_keys_to_snake_case(camel_case_dict):
        sdict = {}
        try:
            for k, v in camel_case_dict.iteritems():
                key = IO.first_cap_re.sub(r'\1_\2', k)
                key = IO.all_cap_re.sub(r'\1_\2', key).lower()

                sdict[key] = IO.dict_keys_to_snake_case(v)
        except AttributeError:  # input is not a dict, return
            sdict = camel_case_dict

        return sdict

    @staticmethod
    def dict_keys_to_camel_case(snake_case_dict):
        cdict = {}
        try:
            for k, v in snake_case_dict.iteritems():
                components = k.split('_')
                key = "".join(x.title() for x in components)

                cdict[key] = IO.dict_keys_to_camel_case(v)
        except AttributeError:  # input is not a dict, return
            cdict = snake_case_dict

        return cdict

    @staticmethod
    def _change_key_first_letter(change_dict, operation):
        cdict = {}
        try:
            for k, v in change_dict.iteritems():
                cdict[getattr(k[:1], operation)() + k[1:]] = \
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
    def to_json(features, filepath=None):
        if filepath is None:
            return json.dumps(features, indent=4)
        else:
            json.dump(features, open(filepath, 'w'), indent=4)

    @staticmethod
    def _from_format(input_str, input_format):
        try:  # file given
            return eval(input_format + ".load(open(input_str))")
        except IOError:  # string given
            return eval(input_format + ".load(input_str)")

    @staticmethod
    def from_pickle(input_str):
        return IO._from_format(input_str, 'pickle')

    @staticmethod
    def from_json(input_str):
        return IO._from_format(input_str, 'json')
