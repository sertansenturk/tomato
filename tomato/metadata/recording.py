import eyed3
from . attribute import Attribute
from . work import Work
from . instrumentationvoicing import InstrumentationVoicing
import musicbrainzngs as mb
from six import iteritems
import logging
logging.basicConfig(level=logging.INFO)

# set the agent to communicate with MusicBrainz
mb.set_useragent("Makam corpus metadata", "1.2.1", "compmusic.upf.edu")

# set logging to report on the error level
try:  # handle different eyeD3 versions
    eyed3.utils.log.log.setLevel(logging.ERROR)
except AttributeError:
    eyed3.log.setLevel("ERROR")


class Recording(object):
    def __init__(self, get_work_attributes=True, print_warnings=None):
        self.print_warnings = print_warnings
        self.get_work_attributes = get_work_attributes

    def from_musicbrainz(self, audio_in):
        try:  # audio file input
            mbid, duration, sampling_frequency, bit_rate = \
                Recording.get_file_metadata(audio_in)
            audio_meta = {'mbid': mbid, 'path': audio_in, 'duration': duration,
                          'sampling_frequency': sampling_frequency,
                          'bit_rate': bit_rate}
        except (IOError, AttributeError):
            audio_meta = {'mbid': audio_in}
        audio_meta['url'] = u'http://musicbrainz.org/recording/{}'.format(
            audio_meta['mbid'])

        meta = mb.get_recording_by_id(
            audio_meta['mbid'], includes=['artists', 'artist-rels', 'releases',
                                          'tags', 'work-rels'])['recording']
        audio_meta['title'] = meta['title']

        # releases
        audio_meta['releases'] = self._get_releases(meta)

        # artist credits
        audio_meta['artist_credits'] = self._get_artist_credits(meta)

        # performers
        audio_meta['artists'] = self._get_artist_relations(meta)

        # works
        if 'work-relation-list' in meta.keys():  # has work
            audio_meta['works'] = self._get_works(meta)

        # get makam/usul/for from work attributes
        if self.get_work_attributes and 'works' in audio_meta.keys():
            self._get_attributes_from_works(audio_meta)

        # get makam/usul/for tags
        self._get_recording_attribute_tags(audio_meta, meta)

        # infer voicing/instrumentation
        audio_meta['instrumentation_voicing'] = InstrumentationVoicing.\
            get_voicing_instrumentation(audio_meta)

        return audio_meta

    def _get_attributes_from_works(self, audio_meta):
        work_metadata = Work(print_warnings=self.print_warnings)
        attribute_keys = ['makam', 'form', 'usul']
        for w in audio_meta['works']:
            work_meta = work_metadata.from_musicbrainz(w['mbid'])
            for ak in attribute_keys:
                if ak not in audio_meta.keys():
                    audio_meta[ak] = work_meta[ak]
                else:
                    for wm in work_meta[ak]:
                        audio_meta[ak].append(wm)

    @staticmethod
    def _get_recording_attribute_tags(audio_meta, meta):
        attributetags = Attribute.get_attrib_tags(meta)
        for key, vals in iteritems(attributetags):
            for val in vals:  # add the source
                val['source'] = 'http://musicbrainz.org/recording/' + \
                                audio_meta['mbid']

            if key not in audio_meta.keys():
                audio_meta[key] = vals
            else:
                for val in vals:
                    audio_meta[key].append(val)

    @staticmethod
    def get_file_metadata(filepath):
        audiofile = eyed3.load(filepath)
        mbid = audiofile.tag.unique_file_ids.get(
            'http://musicbrainz.org').data[-36:]
        duration = audiofile.info.time_secs
        sampling_frequency = audiofile.info.sample_freq
        bit_rate = audiofile.info.mp3_header.bit_rate

        return mbid, duration, sampling_frequency, bit_rate

    @staticmethod
    def _get_releases(meta):
        return [{'title': rel['title'], 'mbid': rel['id']} for rel in
                meta['release-list']]

    @staticmethod
    def _get_artist_credits(meta):
        artist_credits = []
        for credit in meta['artist-credit']:
            try:
                artist_credits.append({'name': credit['artist']['name'],
                                       'mbid': credit['artist']['id']})
            except TypeError:
                logging.debug('skip join phrase')

        return artist_credits

    @staticmethod
    def _get_artist_relations(meta):
        artists = []
        if 'artist-relation-list' in meta.keys():
            for artist in meta['artist-relation-list']:
                artists.append({'name': artist['artist']['name'],
                                'mbid': artist['artist']['id'],
                                'type': artist['type']})
                is_performer = artist['type'] in ['vocal', 'instrument']
                if is_performer and 'attribute-list' in artist.keys():
                    artists[-1]['attribute-list'] = artist['attribute-list']
        return artists

    @staticmethod
    def _get_works(meta):
        return ([{'title': work['work']['title'], 'mbid': work['work']['id']}
                 for work in meta['work-relation-list']])
