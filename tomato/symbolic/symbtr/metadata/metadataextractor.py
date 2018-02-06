import os
import json
import warnings
from .mu2 import Mu2Metadata
from .musicbrainz import MusicBrainzMetadata


class MetadataExtractor(object):
    """

    """
    def __init__(self, get_recording_rels=False):
        self._mb_metadata = MusicBrainzMetadata(
            get_recording_rels=get_recording_rels)

    @property
    def get_recording_rels(self):
        return self._mb_metadata.get_recording_rels

    @get_recording_rels.setter
    def get_recording_rels(self, value):
        self._mb_metadata.get_recording_rels = value

    @staticmethod
    def get_slugs(scorename):
        splitted = scorename.split('--')
        return {'makam': splitted[0], 'form': splitted[1], 'usul': splitted[2],
                'name': splitted[3], 'composer': splitted[4]}

    def get_metadata(self, scorename, mbid=None):
        data = self._mb_metadata.crawl_musicbrainz(mbid)

        data['symbtr'] = scorename

        slugs = MetadataExtractor.get_slugs(scorename)
        for attr in ['makam', 'form', 'usul']:
            self.add_attribute_slug(data, slugs, attr)

        if 'work' in data.keys():
            data['work']['symbtr_slug'] = slugs['name']
        elif 'recording' in data.keys():
            data['recording']['symbtr_slug'] = slugs['name']

        if 'composer' in data.keys():
            data['composer']['symbtr_slug'] = slugs['composer']

        # get and validate the attributes
        is_attr_meta_valid = self.validate_makam_form_usul(data, scorename)

        # get the tonic
        makam = self._get_attr(data['makam']['symbtr_slug'], 'makam')
        data['tonic'] = makam['karar_symbol']

        return data, is_attr_meta_valid

    @classmethod
    def add_attribute_slug(cls, data, slugs, attr):
        if attr in slugs.keys():
            if attr not in data.keys():
                data[attr] = {}
            data[attr]['symbtr_slug'] = slugs[attr]
            data[attr]['attribute_key'] = cls._get_attribute_key(
                data[attr]['symbtr_slug'], attr)

    @classmethod
    def validate_makam_form_usul(cls, data, scorename):
        is_valid_list = []
        for attr in ['makam', 'form', 'usul']:
            is_valid_list.append(cls._validate_attributes(
                data, scorename, attr))

        return all(is_valid_list)

    @staticmethod
    def _get_attribute_key(attr_str, attr_type):
        attr_dict = MetadataExtractor.get_attribute_dict(attr_type)
        for attr_key, attr_val in attr_dict.iteritems():
            if attr_val['symbtr_slug'] == attr_str:
                return attr_key

    @classmethod
    def _validate_attributes(cls, data, scorename, attrib_name):
        score_attrib = data[attrib_name]

        attrib_dict = cls._get_attr(score_attrib['symbtr_slug'],
                                    attrib_name)

        slug_valid = cls._validate_slug(
            attrib_dict, score_attrib, scorename)

        mu2_valid = Mu2Metadata.validate_mu2_attribute(
            score_attrib, attrib_dict, scorename)

        mb_attr_valid = MusicBrainzMetadata.validate_mb_attribute(
            attrib_dict, score_attrib, scorename)

        mb_tag_valid = MusicBrainzMetadata.validate_mb_attribute_tag(
            attrib_dict, score_attrib, scorename)

        return all([slug_valid, mu2_valid, mb_attr_valid, mb_tag_valid])

    @staticmethod
    def _validate_slug(attrib_dict, score_attr, scorename):
        has_slug = 'symbtr_slug' in score_attr.keys()
        if has_slug and not score_attr['symbtr_slug'] ==\
                attrib_dict['symbtr_slug']:
            warnings.warn(u'{0!s}, {1!s}: The slug does not match.'.
                          format(scorename, score_attr['symbtr_slug']),
                          stacklevel=2)
            return False

        return True

    @staticmethod
    def get_attribute_dict(attrstr):
        attrfile = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), '..', 'makam_data', attrstr + '.json')

        return json.load(open(attrfile, 'r'))

    @classmethod
    def validate_key_signature(cls, key_signature, makam_slug, symbtr_name):
        attr_dict = MetadataExtractor.get_attribute_dict('makam')
        key_sig_makam = attr_dict[makam_slug]['key_signature']

        # the number of accidentals should be the same
        is_key_sig_valid = len(key_signature) == len(key_sig_makam)

        # the sequence should be the same, allow a single comma deviation
        # due to AEU theory and practice mismatch
        for k1, k2 in zip(key_signature, key_sig_makam):
            is_key_sig_valid = (is_key_sig_valid and
                                cls._compare_accidentals(k1, k2))

        if not is_key_sig_valid:
            warnings.warn(u'{0!s}: Key signature is different! {1!s} -> {2!s}'.
                          format(symbtr_name, ' '.join(key_signature),
                                 ' '.join(key_sig_makam)), stacklevel=2)

        return is_key_sig_valid

    @staticmethod
    def _compare_accidentals(acc1, acc2):
        same_acc = True
        if acc1 == acc2:  # same note
            pass
        elif acc1[:3] == acc2[:3]:  # same note symbol
            if abs(int(acc1[3:]) - int(acc2[3:])) <= 1:  # 1 comma deviation
                pass
            else:  # more than one comma deviation
                same_acc = False
        else:  # different notes
            same_acc = False

        return same_acc

    @staticmethod
    def _get_attr(slug, attr_name):
        attr_dict = MetadataExtractor.get_attribute_dict(attr_name)

        for attr in attr_dict.values():
            if attr['symbtr_slug'] == slug:
                return attr

        # no match
        return {}
