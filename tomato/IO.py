import tempfile
import os
from six import iteritems
from json_tricks import np as json
import pickle
import re
import logging


class IO(object):
    @staticmethod
    def get_public_attr(generic_obj):
        return [name for name in generic_obj.__dict__.keys()
                if not name.startswith('_')]

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
                raise Exception(u'Missing output {0:s} file'.format(exp))

        return out_dict

    # compiled regular expressions for dict_keys_to_snake_case
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    @staticmethod
    def dict_keys_to_snake_case(camel_case_dict):
        sdict = {}
        try:
            for k, v in iteritems(camel_case_dict):
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
            for k, v in iteritems(snake_case_dict):
                components = k.split('_')
                key = "".join(x.title() for x in components)

                cdict[key] = IO.dict_keys_to_camel_case(v)
        except AttributeError:  # input is not a dict, return
            cdict = snake_case_dict

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
    def from_pickle(input_str):
        try:  # file given
            return pickle.load(open(input_str, 'rb'))
        except IOError:  # string given
            return pickle.loads(input_str, 'rb')

    @staticmethod
    def from_json(input_str):
        try:  # file given
            return json.load(open(input_str, 'r'), preserve_order=False)
        except IOError:  # string given
            return json.loads(input_str, 'r', preserve_order=False)
