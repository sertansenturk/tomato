import json
import logging
from ..io import IO

logging.basicConfig(level=logging.INFO)


class Attribute(object):
    @staticmethod
    def _get_attrib_dict(attrstr):
        return IO.load_music_theory(attrstr)

    @classmethod
    def get_attr_key_from_mb_attr(cls, attr_str, attr_type):
        attr_dict = IO.load_music_theory(attr_type)
        for attr_key, attr_val in attr_dict.items():
            if attr_val['dunya_name'] == attr_str:
                return attr_key

    @classmethod
    def _get_attr_key_from_mb_tag(cls, attr_str, attr_type):
        attr_dict = IO.load_music_theory(attr_type)
        for attr_key, attr_val in attr_dict.items():
            if attr_str in attr_val['mb_tag']:
                return attr_key

    @classmethod
    def get_attrib_tags(cls, meta):
        theory_attribute_keys = ['makam', 'form', 'usul']
        attributes = dict()
        if 'tag-list' in meta.keys():
            for k in theory_attribute_keys:  # for makam/form/usul keys
                for t in meta['tag-list']:  # for each tag
                    try:  # attempt to assign the tag to the attribute key
                        cls._assign_attrib(attributes, k, t)
                    except ValueError:
                        logging.debug(u'{0:s} is not a makam/form/usul tag; '
                                      u'skipped'.format(t))
        return attributes

    @classmethod
    def _assign_attrib(cls, attributes, k, t):
        key, val = t['name'].split(': ')
        if k in key:
            if k not in attributes.keys():  # create the key
                attributes[k] = []

            attributes[k].append(
                {'mb_tag': val, 'attribute_key':
                    cls._get_attr_key_from_mb_tag(val, k)})
