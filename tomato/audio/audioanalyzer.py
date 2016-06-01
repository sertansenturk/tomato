import numpy as np
from copy import deepcopy
import timeit
import six

from makammusicbrainz.audiometadata import AudioMetadata
from predominantmelodymakam.predominantmelodymakam import \
    PredominantMelodyMakam
from pitchfilter.pitchfilter import PitchFilter
from seyiranalyzer.audioseyiranalyzer import AudioSeyirAnalyzer
from tonicidentifier.toniclastnote import TonicLastNote
from ahenkidentifier.ahenkidentifier import AhenkIdentifier
from notemodel.notemodel import NoteModel
from morty.pitchdistribution import PitchDistribution
from musicbrainzngs import NetworkError
from musicbrainzngs import ResponseError

from ..analyzer import Analyzer
from ..plotter import Plotter
from ..io import IO

import warnings
import logging
logging.basicConfig(level=logging.INFO)


class AudioAnalyzer(Analyzer):
    _inputs = ['makam', 'melodic_progression', 'metadata', 'note_models',
               'pitch', 'pitch_class_distribution', 'pitch_distribution',
               'pitch_filtered', 'tempo', 'tonic', 'transposition']

    def __init__(self, verbose=False):
        super(AudioAnalyzer, self).__init__(verbose=verbose)

        # settings that are not defined in the respective classes
        self._pd_params = {'kernel_width': 7.5, 'step_size': 7.5}
        # - for melodic progression None means, applying the rule of thumb
        #   defined in the method "compute_melodic_progression". This class has
        #   two parameters defined in init and the other two defined in the
        #   method call. Here we only store the ones called in the method call.
        self._mel_prog_params = {'frame_dur': None, 'hop_ratio': 0.5,
                                 'min_num_frames': 40, 'max_frame_dur': 30}

        # extractors
        self._metadata_getter = AudioMetadata(get_work_attributes=True)
        self._pitch_extractor = PredominantMelodyMakam(filter_pitch=False)
        self._pitch_filter = PitchFilter()
        self._melodic_progression_analyzer = AudioSeyirAnalyzer()
        self._tonic_identifier = TonicLastNote()
        self._note_modeler = NoteModel()

    def analyze(self, filepath=None, **kwargs):
        audio_f = self._parse_inputs(**kwargs)

        # metadata
        audio_f['metadata'] = self._call_audio_metadata(audio_f['metadata'],
                                                        filepath)

        # predominant melody extraction
        audio_f['pitch'] = self._partial_caller(audio_f['pitch'],
                                                self.extract_pitch, filepath)

        # pitch filtering
        audio_f['pitch_filtered'] = self._partial_caller(
            audio_f['pitch_filtered'], self.filter_pitch, audio_f['pitch'])

        # get the melodic progression
        audio_f['melodic_progression'] = self._partial_caller(
            audio_f['melodic_progression'], self.compute_melodic_progression,
            audio_f['pitch_filtered'])

        # tonic identification
        audio_f['tonic'] = self._partial_caller(
            audio_f['tonic'], self.identify_tonic, audio_f['pitch_filtered'])

        # histogram computation
        audio_f['pitch_distribution'] = self._partial_caller(
            audio_f['pitch_distribution'], self.compute_pitch_distribution,
            audio_f['pitch_filtered'])
        try:
            audio_f['pitch_class_distribution'] = \
                audio_f['pitch_distribution'].to_pcd()
        except KeyError:
            logging.info('Pitch class distribution computation failed.')

        # makam recognition
        # TODO: allow multiple makams
        audio_f['makam'] = self._partial_caller(
            audio_f['makam'], self.get_makams, audio_f['metadata'],
            audio_f['pitch_class_distribution'])
        audio_f['makam'] = self._partial_caller(
            None, self._get_first, audio_f['makam'])

        # transposition (ahenk) identification
        # TODO: allow transpositions for multiple makams
        audio_f['transposition'] = self._partial_caller(
            audio_f['transposition'], self.identify_transposition,
            audio_f['tonic'], audio_f['makam'])

        # note models
        # TODO: check if there is more than one transposition name, if yes warn
        audio_f['note_models'] = self._partial_caller(
            audio_f['note_models'], self.compute_note_models,
            audio_f['pitch_distribution'], audio_f['tonic'], audio_f['makam'])

        # return as a dictionary
        return audio_f

    def _call_audio_metadata(self, audio_meta, filepath):
        if audio_meta is False:  # metadata crawling is disabled
            audio_meta = None
        elif audio_meta is None:  # no MBID is given, attempt to get
            # it from id3 tag
            audio_meta = self.crawl_musicbrainz_metadata(
                filepath)
        elif isinstance(audio_meta, (six.string_types, six.binary_type)):
            # MBID is given
            audio_meta = self.crawl_musicbrainz_metadata(
                audio_meta)
        elif not isinstance(audio_meta, dict):
            warn_str = 'The "metadata" input can be "False" (skipped), ' \
                       '"basestring" (MBID input), "None" (attempt to get ' \
                       'the MBID from audio file tags) or "dict" (already ' \
                       'computed)'
            warnings.warn(warn_str, stacklevel=2)
        return audio_meta

    def get_makams(self, metadata, pitch_class_distribution):
        try:  # try to get the makam from the metadata
            makams = list(set(m['attribute_key'] for m in metadata['makam']))

        except (TypeError, KeyError):
            # metadata is not available or the makam is not known
            makams = self.recognize_makam(pitch_class_distribution)

        return makams

    def crawl_musicbrainz_metadata(self, rec_in):
        try:
            tic = timeit.default_timer()
            self.vprint(u"- Getting relevant metadata of {0:s}".format(rec_in))
            audio_meta = self._metadata_getter.from_musicbrainz(rec_in)

            self.vprint_time(tic, timeit.default_timer())
            return audio_meta
        except (NetworkError, ResponseError):
            warnings.warn('Unable to reach http://musicbrainz.org/. '
                          'The metadata stored there is not crawled.',
                          RuntimeWarning, stacklevel=2)
            return None

    def extract_pitch(self, filename):
        tic = timeit.default_timer()
        self.vprint(u"- Extracting predominant melody of {0:s}".
                    format(filename))

        results = self._pitch_extractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        self.vprint_time(tic, timeit.default_timer())
        return pitch

    def filter_pitch(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Filtering predominant melody of {0:s}".
                    format(pitch['source']))

        pitch_filt = deepcopy(pitch)
        pitch_filt['pitch'] = self._pitch_filter.run(pitch_filt['pitch'])
        pitch_filt['citation'] = 'Bozkurt, B. (2008). An automatic pitch ' \
                                 'analysis method for Turkish maqam music. ' \
                                 'Journal of New Music Research, 37(1), 1-13.'

        self.vprint_time(tic, timeit.default_timer())
        return pitch_filt

    def compute_melodic_progression(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Computing the melodic progression model of {0:s}"
                    .format(pitch['source']))

        if self._mel_prog_params['frame_dur'] is None:
            # compute number of frames from some simple "rule of thumb"
            duration = pitch['pitch'][-1][0]
            frame_dur = duration / self._mel_prog_params['min_num_frames']
            frame_dur = int(5 * round(float(frame_dur) / 5))  # round to 5sec

            # force to be between 5 and max_frame_dur
            if frame_dur < 5:
                frame_dur = 5
            elif frame_dur > self._mel_prog_params['max_frame_dur']:
                frame_dur = self._mel_prog_params['max_frame_dur']
        else:
            frame_dur = self._mel_prog_params['frame_dur']

        melodic_progression = self._melodic_progression_analyzer.analyze(
            pitch['pitch'], frame_dur=frame_dur,
            hop_ratio=self._mel_prog_params['hop_ratio'])
        self.vprint_time(tic, timeit.default_timer())

        return melodic_progression

    def identify_tonic(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Identifying tonic from the predominant melody of {0:s}"
                    .format(pitch['source']))

        tonic = self._tonic_identifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        self.vprint_time(tic, timeit.default_timer())
        return tonic

    def compute_pitch_distribution(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Computing pitch distribution of {0:s}".
                    format(pitch['source']))

        pitch_distribution = PitchDistribution.from_hz_pitch(
            np.array(pitch['pitch'])[:, 1],
            kernel_width=self._pd_params['kernel_width'],
            step_size=self._pd_params['step_size'])
        pitch_distribution.cent_to_hz()

        self.vprint_time(tic, timeit.default_timer())
        return pitch_distribution

    def compute_class_pitch_distribution(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Computing pitch class distribution of {0:s}".format(
            pitch['source']))

        pitch_class_distribution = self.compute_pitch_distribution(
            pitch).to_pcd()

        self.vprint_time(tic, timeit.default_timer())
        return pitch_class_distribution

    def recognize_makam(self, pitch_class_distribution):
        tic = timeit.default_timer()
        self.vprint(u"- Recognizing the makam of {0:s}".format(
            pitch_class_distribution['source']))
        # metadata is not available or the makam is not known
        warnings.warn('Makam recognition is not integrated yet.',
                      FutureWarning, stacklevel=2)

        self.vprint_time(tic, timeit.default_timer())
        return None

    def identify_transposition(self, tonic, makam_tonic_str):
        tic = timeit.default_timer()
        self.vprint(u"- Identifying the transposition of {0:s}".format(
            tonic['source']))
        transposition = AhenkIdentifier.identify(
            tonic['value'], makam_tonic_str)
        transposition['source'] = tonic['source']

        self.vprint_time(tic, timeit.default_timer())
        return transposition

    def compute_note_models(self, pitch_distribution, tonic, makamstr):
        tic = timeit.default_timer()
        self.vprint(u"- Computing the note models for {0:s}".
                    format(tonic['source']))

        note_models = self._note_modeler.calculate_notes(
            pitch_distribution, tonic['value'], makamstr)
        self.vprint_time(tic, timeit.default_timer())
        return note_models

    # setters
    def set_pitch_extractor_params(self, **kwargs):
        self._set_params('_pitch_extractor', **kwargs)

    def set_metadata_getter_params(self, **kwargs):
        self._set_params('_metadata_getter', **kwargs)

    def set_pitch_filter_params(self, **kwargs):
        self._set_params('_pitch_filter', **kwargs)

    def set_pitch_distibution_params(self, **kwargs):
        self._set_params('_pd_params', **kwargs)

    def set_tonic_identifier_params(self, **kwargs):
        self._set_params('_tonic_identifier', **kwargs)

    def set_melody_progression_params(self, **kwargs):
        method_params = self._mel_prog_params.keys()  # imput parameters
        obj_params = IO.public_noncallables(self._melodic_progression_analyzer)

        Analyzer.chk_params(method_params + obj_params, kwargs)
        for key, value in kwargs.items():
            if key in method_params:
                self._mel_prog_params[key] = value
            elif key in obj_params:
                setattr(self._melodic_progression_analyzer, key, value)
            else:
                raise KeyError("Unexpected key error")

    def set_note_modeler_params(self, **kwargs):
        self._set_params('_note_modeler', **kwargs)

    # plot
    @staticmethod
    def plot(audio_features):
        pitch = audio_features['pitch_filtered']['pitch']
        pitch_distribution = audio_features['pitch_distribution']
        note_models = audio_features['note_models']
        melodic_progression = audio_features['melodic_progression']
        makam = audio_features['makam']
        tonic = audio_features['tonic']
        transposition = audio_features['transposition']
        try:
            tempo = audio_features['tempo']
        except KeyError:
            tempo = None

        return Plotter.plot_audio_features(
            pitch=pitch, pitch_distribution=pitch_distribution,
            note_models=note_models, melodic_progression=melodic_progression,
            makam=makam, tonic=tonic, transposition=transposition, tempo=tempo)
