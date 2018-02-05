from . attribute import Attribute
import json
import warnings
import urllib

import musicbrainzngs as mb
mb.set_useragent("Makam corpus metadata", "1.2.0", "compmusic.upf.edu")


class WorkMetadata(object):
    def __init__(self, get_recording_rels=True, print_warnings=None):
        self.get_recording_rels = get_recording_rels
        self.print_warnings = print_warnings

    def from_musicbrainz(self, mbid):
        included_rels = (['artist-rels', 'recording-rels']
                         if self.get_recording_rels else ['artist-rels'])
        work = mb.get_work_by_id(mbid, includes=included_rels)['work']

        data = {'makam': [], 'form': [], 'usul': [], 'title': work['title'],
                'mbid': mbid, 'composer': dict(), 'lyricist': dict(),
                'url': 'http://musicbrainz.org/work/' + mbid, 'language': ''}

        # assign makam, form, usul attributes to data
        self._assign_makam_form_usul(data, mbid, work)

        # language
        self._assign_language(data, work)

        # composer and lyricist
        self._assign_composer_lyricist(data, work)

        # add recordings
        self._assign_recordings(data, work)

        # add scores
        self._add_scores(data, mbid)

        # warnings
        self._chk_warnings(data)

        return data

    @staticmethod
    def _add_scores(data, mbid):
        score_work_url = 'https://raw.githubusercontent.com/MTG/SymbTr/' \
                         'master/symbTr_mbid.json'
        response = urllib.urlopen(score_work_url)
        score_work = json.loads(response.read())
        data['scores'] = []
        for sw in score_work:
            if mbid in sw['uuid']:
                data['scores'].append(sw['name'])

    def _chk_warnings(self, data):
        if self.print_warnings:
            self._chk_data_key_exists(data, dkey='makam')
            self._chk_data_key_exists(data, dkey='form')
            self._chk_data_key_exists(data, dkey='usul')
            self._chk_data_key_exists(data, dkey='composer')

            if 'language' in data.keys():  # language entered to MusicBrainz
                self._chk_lyricist(data)
            else:  # no lyrics information in MusicBrainz
                self._chk_language(data)

    @staticmethod
    def _chk_language(data):
        if data['lyricist']:  # lyricist available
            warnings.warn(u'http://musicbrainz.org/work/{0:s} Language of the '
                          u'vocal work is not entered!'.format(data['mbid']),
                          stacklevel=2)
        else:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} Language is not '
                          u'entered!'.format(data['mbid']), stacklevel=2)

    @staticmethod
    def _chk_lyricist(data):
        if data['language'] == "zxx":  # no lyrics
            if data['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'entered to the instrumental work!'.
                              format(data['mbid']), stacklevel=2)
        else:  # has lyrics
            if not data['lyricist']:
                warnings.warn(u'http://musicbrainz.org/work/{0:s} Lyricist is '
                              u'not entered!'.format(data['mbid']),
                              stacklevel=2)

    @staticmethod
    def _chk_data_key_exists(data, dkey):
        if not data[dkey]:
            warnings.warn(u'http://musicbrainz.org/work/{0:s} {1:s} is not '
                          u'entered!'.format(data['mbid'], dkey.title()),
                          stacklevel=2)

    @staticmethod
    def _assign_recordings(data, work):
        data['recordings'] = []
        if 'recording-relation-list' in work.keys():
            for r in work['recording-relation-list']:
                data['recordings'].append({'mbid': r['recording']['id'],
                                           'title': r['recording']['title']})

    @staticmethod
    def _assign_composer_lyricist(data, work):
        if 'artist-relation-list' in work.keys():
            for a in work['artist-relation-list']:
                if a['type'] in ['composer', 'lyricist']:
                    data[a['type']] = {'name': a['artist']['name'],
                                       'mbid': a['artist']['id']}

    @staticmethod
    def _assign_language(data, work):
        if 'language' in work.keys():
            data['language'] = work['language']

    @classmethod
    def _assign_makam_form_usul(cls, data, mbid, work):
        if 'attribute-list' in work.keys():
            w_attrb = work['attribute-list']
            for attr_name in ['makam', 'form', 'usul']:
                cls._assign_attr(data, mbid, w_attrb, attr_name)

    @staticmethod
    def _assign_attr(data, mbid, w_attrb, attrname):
        attr = [a['value'] for a in w_attrb
                if attrname.title() in a['attribute']]
        data[attrname] = [
            {'mb_attribute': m,
             'attribute_key': Attribute.get_attr_key_from_mb_attr(m, attrname),
             'source': 'http://musicbrainz.org/work/' + mbid}
            for m in attr]
