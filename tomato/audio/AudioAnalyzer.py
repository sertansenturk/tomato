import numpy as np
from copy import deepcopy

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

    def analyze(self, filepath, makam=None, mbid=None):
        # metadata
        meta_in = mbid if mbid is not None else filepath
        try:
            metadata = self.get_musicbrainz_metadata(meta_in)
        except (NetworkError, ResponseError):
            metadata = None
            warnings.warn('Unable to reach http://musicbrainz.org/. '
                          'The metadata stored there is not crawled.',
                          RuntimeWarning)

        # predominant melody extraction
        pitch = self.extract_pitch(filepath)

        # pitch filtering
        pitch_filtered = self.filter_pitch(pitch)

        # get the melodic prograssion model
        melodic_progression = self.get_melodic_progression(pitch_filtered)

        # tonic identification
        tonic = self.identify_tonic(pitch_filtered)

        # histogram computation
        pitch_distribution = self.compute_pitch_distribution(
            pitch_filtered, tonic)
        pitch_distribution.cent_to_hz()
        pitch_class_distribution = pitch_distribution.to_pcd()

        # makam recognition
        # TODO: allow multiple makams
        makam = self._get_makam(makam, metadata, pitch_class_distribution)

        # transposition (ahenk) identification
        # TODO: allow transpositions for multiple makams
        try:
            transposition = self.identify_transposition(tonic, makam)
        except ValueError as e:
            transposition = None
            warnings.warn(e.message, RuntimeWarning)

        # tuning analysis and stable pitch extraction
        # TODO: check if there is more than one transposition name, if yes warn
        try:
            stable_notes = self.get_stable_notes(pitch_distribution, tonic,
                                                 makam)
        except KeyError as e:
            stable_notes = None
            warnings.warn(e.message, RuntimeWarning)

        # return as a dictionary
        return {'metadata': metadata, 'pitch': pitch,
                'pitch_filtered': pitch_filtered, 'tonic': tonic,
                'transposition': transposition, 'makam': makam,
                'melodic_progression': melodic_progression,
                'pitch_distribution': pitch_distribution,
                'pitch_class_distribution': pitch_class_distribution,
                'stable_notes': stable_notes}

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
        self.vprint(u"- Getting relevant metadata of {0:s}".format(rec_in))
        return (None if rec_in is False
                else self._metadataGetter.from_musicbrainz(rec_in))

    def extract_pitch(self, filename):
        self.vprint(u"- Extracting predominant melody of {0:s}".
                    format(filename))

        results = self._pitchExtractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def filter_pitch(self, pitch):
        self.vprint(u"- Filtering predominant melody of {0:s}".
                    format(pitch['source']))

        pitch_filt = deepcopy(pitch)
        pitch_filt['pitch'] = self._pitchFilter.run(pitch_filt['pitch'])
        pitch_filt['citation'] = 'Bozkurt, B. (2008). An automatic pitch ' \
                                 'analysis method for Turkish maqam music. ' \
                                 'Journal of New Music Research, 37(1), 1-13.'

        return pitch_filt

    def get_melodic_progression(self, pitch):
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

        return self._melodicProgressionAnalyzer.analyze(
            pitch['pitch'], frame_dur=frame_dur,
            hop_ratio=self._mel_prog_params['hop_ratio'])

    def identify_tonic(self, pitch):
        self.vprint(u"- Identifying tonic from the predominant melody of {0:s}"
                    .format(pitch['source']))

        tonic = self._tonicIdentifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        return tonic

    def compute_pitch_distribution(self, pitch, tonic):
        self.vprint(u"- Computing pitch distribution of {0:s}".
                    format(pitch['source']))

        return PitchDistribution.from_hz_pitch(
            np.array(pitch['pitch'])[:, 1], ref_freq=tonic['value'],
            smooth_factor=self._pd_params['kernel_width'],
            step_size=self._pd_params['step_size'])

    def compute_class_pitch_distribution(self, pitch, tonic):
        self.vprint(u"- Computing pitch class distribution of {0:s}".format(
            pitch['source']))

        return self.compute_pitch_distribution(pitch, tonic).to_pcd()

    def recognize_makam(self, pitch_class_distribution):
        # metadata is not available or the makam is not known
        warnings.warn('Makam recognition is not integrated yet.',
                      FutureWarning)
        return None

    def identify_transposition(self, tonic, makam_tonic_str):
        self.vprint(u"- Identifying the transposition of {0:s}".format(
            tonic['source']))
        transposition = AhenkIdentifier.identify(
            tonic['value'], makam_tonic_str)
        transposition['source'] = tonic['source']

        return transposition

    def get_stable_notes(self, pitch_distribution, tonic, makamstr):
        self.vprint(u"- Obtaining the stable notes of {0:s}".
                    format(tonic['source']))

        return self._noteModeler.calculate_notes(pitch_distribution,
                                                 tonic['value'], makamstr)

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
        note_models = deepcopy(features['stable_notes'])
        melodic_progression = deepcopy(features['melodic_progression'])

        return Plotter.plot_audio_features(
            pitch=pitch, pitch_distribution=pitch_distribution,
            note_models=note_models, melodic_progression=melodic_progression)
