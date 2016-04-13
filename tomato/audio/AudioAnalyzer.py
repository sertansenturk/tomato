import numpy as np
from copy import deepcopy
import timeit
from six import iteritems

from makammusicbrainz.AudioMetadata import AudioMetadata
from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam
from pitchfilter.PitchFilter import PitchFilter
from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer
from tonicidentifier.TonicLastNote import TonicLastNote
from ahenkidentifier.AhenkIdentifier import AhenkIdentifier
from notemodel.NoteModel import NoteModel
from modetonicestimation.PitchDistribution import PitchDistribution
from musicbrainzngs import NetworkError
from musicbrainzngs import ResponseError

from tomato.Analyzer import Analyzer
from tomato.Plotter import Plotter

import warnings
import logging
logging.basicConfig(level=logging.INFO)


class AudioAnalyzer(Analyzer):
    audio_features = [
        'metadata', 'pitch', 'pitch_filtered', 'melodic_progression', 'tonic',
        'transposition', 'pitch_distribution', 'pitch_class_distribution',
        'makam', 'stable_notes']

    def __init__(self, verbose=False):
        super(AudioAnalyzer, self).__init__(verbose=verbose)

        # settings that are not defined in the respective classes
        self._pd_params = {'kernel_width': 7.5, 'step_size': 7.5}
        # - for melodic progression None means, applying the rule of thumb
        #   defined in the method "get_melodic_progression". This class has
        #   two parameters defined in init and the other two defined in the
        #   method call. Here we only store the ones called in the method call.
        self._mel_prog_params = {'frame_dur': None, 'hop_ratio': 0.5,
                                 'min_num_frames': 40, 'max_frame_dur': 30}

        # extractors
        self._metadataGetter = AudioMetadata(get_work_attributes=True)
        self._pitchExtractor = PredominantMelodyMakam(filter_pitch=False)
        self._pitchFilter = PitchFilter()
        self._melodicProgressionAnalyzer = AudioSeyirAnalyzer()
        self._tonicIdentifier = TonicLastNote()
        self._noteModeler = NoteModel()

    def analyze(self, filepath=None, mbid=None, **kwargs):
        audio_features = self._parse_inputs(**kwargs)

        # metadata
        meta_in = mbid if mbid is not None else filepath
        try:
            audio_features['metadata'] = self.get_musicbrainz_metadata(meta_in)
        except (NetworkError, ResponseError):
            audio_features['metadata'] = None
            warnings.warn('Unable to reach http://musicbrainz.org/. '
                          'The metadata stored there is not crawled.',
                          RuntimeWarning)

        # predominant melody extraction
        audio_features['pitch'] = self.extract_pitch(filepath)

        # pitch filtering
        audio_features['pitch_filtered'] = self.filter_pitch(
            audio_features['pitch'])

        # get the melodic prograssion model
        audio_features['melodic_progression'] = self.get_melodic_progression(
            audio_features['pitch_filtered'])

        # tonic identification
        audio_features['tonic'] = self.identify_tonic(
            audio_features['pitch_filtered'])

        # histogram computation
        audio_features['pitch_distribution'] = self.compute_pitch_distribution(
            audio_features['pitch_filtered'], audio_features['tonic'])
        audio_features['pitch_distribution'].cent_to_hz()
        audio_features['pitch_class_distribution'] = \
            audio_features['pitch_distribution'].to_pcd()

        # makam recognition
        # TODO: allow multiple makams
        audio_features['makam'] = self._get_makam(
            audio_features['makam'], audio_features['metadata'],
            audio_features['pitch_class_distribution'])

        # transposition (ahenk) identification
        # TODO: allow transpositions for multiple makams
        try:
            audio_features['transposition'] = self.identify_transposition(
                audio_features['tonic'], audio_features['makam'])
        except ValueError as e:
            audio_features['transposition'] = None
            warnings.warn(e.message, RuntimeWarning)

        # note models
        # TODO: check if there is more than one transposition name, if yes warn
        try:
            audio_features['note_models'] = self.get_note_models(
                audio_features['pitch_distribution'],
                audio_features['tonic'], audio_features['makam'])
        except KeyError as e:
            audio_features['note_models'] = None
            warnings.warn(e.message, RuntimeWarning)

        # return as a dictionary
        return audio_features

    @staticmethod
    def _parse_inputs(**kwargs):
        # initialize precomputed_features with the avaliable analysis
        precomputed_features = dict((f, None)
                                    for f in AudioAnalyzer.audio_features)
        for feature, val in iteritems(kwargs):
            if feature not in AudioAnalyzer.audio_features:
                warn_str = u'Unknown feature {0:s}. It will be kept, but it ' \
                           u'will not be used in the audio analysis.' \
                           u''.format(feature)
                warnings.warn(warn_str)
            precomputed_features[feature] = val

        return precomputed_features

    def _get_makam(self, makam, metadata, pitch_class_distribution):
        if makam is None:
            try:  # try to get the makam from the metadata
                makams = set(m['attribute_key'] for m in metadata['makam'])

                # for now get the first makam
                makam = list(makams)[0]
            except (TypeError, KeyError):
                # metadata is not available or the makam is not known
                makam = self.recognize_makam(pitch_class_distribution)
        elif isinstance(makam, list):  # list of makams given
            makam = makam[0]  # for now get the first makam

        return makam

    def update_analysis(self, audio_features):
        if audio_features is None:
            warnings.warn('No input audio features are supplied to update. '
                          'Returning None', RuntimeWarning)
            return None

        # check input format
        self.chk_update_analysis_input(audio_features)

        # make a copy of the existing analysis
        up_f = deepcopy(audio_features)

        # Recompute the features, if their inputs are supplied
        # get the melodic progression model
        try:
            up_f['melodic_progression'] = \
                self.get_melodic_progression(up_f['pitch'])
        except KeyError:
            logging.info('Melodic progression computation failed.')

        # histogram computation
        try:
            up_f['pitch_distribution'] = self.compute_pitch_distribution(
                up_f['pitch'], up_f['tonic'])
            up_f['pitch_distribution'].cent_to_hz()
            up_f['pitch_class_distribution'] = \
                up_f['pitch_distribution'].to_pcd()
        except KeyError:
            logging.info('Pitch (class) distribution computation failed.')

        # transposition (ahenk) identification
        try:
            up_f['transposition'] = self.identify_transposition(
                up_f['tonic'], up_f['tonic']['symbol'])
        except KeyError:
            logging.info('Transposition computation failed.')

        return up_f

    @staticmethod
    def chk_update_analysis_input(audio_features):
        if not (isinstance(audio_features, dict) or audio_features is None):
            raise IOError('The audio_features input should be a dictionary '
                          'or "None" for skipping the method')

    def get_musicbrainz_metadata(self, rec_in):
        if rec_in is False:  # metadata crawling is disabled
            return None
        else:
            tic = timeit.default_timer()
            self.vprint(u"- Getting relevant metadata of {0:s}".format(rec_in))
            audio_meta = self._metadataGetter.from_musicbrainz(rec_in)

            self.vprint_time(tic, timeit.default_timer())
            return audio_meta

    def extract_pitch(self, filename):
        tic = timeit.default_timer()
        self.vprint(u"- Extracting predominant melody of {0:s}".
                    format(filename))

        results = self._pitchExtractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        self.vprint_time(tic, timeit.default_timer())
        return pitch

    def filter_pitch(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Filtering predominant melody of {0:s}".
                    format(pitch['source']))

        pitch_filt = deepcopy(pitch)
        pitch_filt['pitch'] = self._pitchFilter.run(pitch_filt['pitch'])
        pitch_filt['citation'] = 'Bozkurt, B. (2008). An automatic pitch ' \
                                 'analysis method for Turkish maqam music. ' \
                                 'Journal of New Music Research, 37(1), 1-13.'

        self.vprint_time(tic, timeit.default_timer())
        return pitch_filt

    def get_melodic_progression(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Obtaining the melodic progression model of {0:s}"
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

        melodic_progression = self._melodicProgressionAnalyzer.analyze(
            pitch['pitch'], frame_dur=frame_dur,
            hop_ratio=self._mel_prog_params['hop_ratio'])
        self.vprint_time(tic, timeit.default_timer())

        return melodic_progression

    def identify_tonic(self, pitch):
        tic = timeit.default_timer()
        self.vprint(u"- Identifying tonic from the predominant melody of {0:s}"
                    .format(pitch['source']))

        tonic = self._tonicIdentifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        self.vprint_time(tic, timeit.default_timer())
        return tonic

    def compute_pitch_distribution(self, pitch, tonic):
        tic = timeit.default_timer()
        self.vprint(u"- Computing pitch distribution of {0:s}".
                    format(pitch['source']))

        pitch_distribution = PitchDistribution.from_hz_pitch(
            np.array(pitch['pitch'])[:, 1], ref_freq=tonic['value'],
            smooth_factor=self._pd_params['kernel_width'],
            step_size=self._pd_params['step_size'])

        self.vprint_time(tic, timeit.default_timer())
        return pitch_distribution

    def compute_class_pitch_distribution(self, pitch, tonic):
        tic = timeit.default_timer()
        self.vprint(u"- Computing pitch class distribution of {0:s}".format(
            pitch['source']))

        pitch_class_distribution = self.compute_pitch_distribution(
            pitch, tonic).to_pcd()

        self.vprint_time(tic, timeit.default_timer())
        return pitch_class_distribution

    def recognize_makam(self, pitch_class_distribution):
        tic = timeit.default_timer()
        self.vprint(u"- Recognizing the makam of {0:s}".format(
            pitch_class_distribution['source']))
        # metadata is not available or the makam is not known
        warnings.warn('Makam recognition is not integrated yet.',
                      FutureWarning)

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

    def get_note_models(self, pitch_distribution, tonic, makamstr):
        tic = timeit.default_timer()
        self.vprint(u"- Computing the note models for {0:s}".
                    format(tonic['source']))

        note_models = self._noteModeler.calculate_notes(
            pitch_distribution, tonic['value'], makamstr)
        self.vprint_time(tic, timeit.default_timer())
        return note_models

    # setters
    def set_pitch_extractor_params(self, **kwargs):
        self._set_params('_pitchExtractor', **kwargs)

    def set_metadata_getter_params(self, **kwargs):
        self._set_params('_metadataGetter', **kwargs)

    def set_pitch_filter_params(self, **kwargs):
        self._set_params('_pitchFilter', **kwargs)

    def set_pitch_distibution_params(self, **kwargs):
        self._set_params('_pd_params', **kwargs)

    def set_tonic_identifier_params(self, **kwargs):
        self._set_params('_tonicIdentifier', **kwargs)

    def set_melody_progression_params(self, **kwargs):
        method_params = self._mel_prog_params.keys()  # imput parameters
        obj_params = self.get_public_attr(self._melodicProgressionAnalyzer)

        Analyzer.chk_params(method_params + obj_params, kwargs)

        for key, value in kwargs.items():
            if key in method_params:
                self._mel_prog_params[key] = value
            elif key in obj_params:
                setattr(self._melodicProgressionAnalyzer, key, value)
            else:
                raise KeyError("Unexpected key error")

    def set_note_modeler_params(self, **kwargs):
        self._set_params('_noteModeler', **kwargs)

    # plot
    @staticmethod
    def plot(features):
        pitch = np.array(deepcopy(features['pitch_filtered']['pitch']))
        pitch[pitch[:, 1] < 20.0, 1] = np.nan  # remove inaudible for plots
        pitch_distribution = deepcopy(features['pitch_distribution'])
        try:  # convert the bins to hz, if they are given in cents
            pitch_distribution.cent_to_hz()
        except ValueError:
            logging.debug('The pitch distribution should already be in hz')
        note_models = deepcopy(features['note_models'])
        melodic_progression = deepcopy(features['melodic_progression'])

        return Plotter.plot_audio_features(
            pitch=pitch, pitch_distribution=pitch_distribution,
            note_models=note_models, melodic_progression=melodic_progression)
