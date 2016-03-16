from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam
from tonicidentifier.TonicLastNote import TonicLastNote
from ahenkidentifier.AhenkIdentifier import AhenkIdentifier
from notemodel.NoteModel import NoteModel
from modetonicestimation.PitchDistribution import PitchDistribution
import numpy as np


class AudioAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._pitchExtractor = PredominantMelodyMakam()
        self._tonicIdentifier = TonicLastNote()
        self._noteModeler = NoteModel()
        self._pd_params = {'smooth_factor': 7.5, 'step_size': 7.5}

    def analyze(self, filepath, makam=None):
        # predominant melody extraction
        # There is no need to run pitch filter as it is run in extract_pitch
        # by default
        pitch = self.extract_pitch(filepath)

        # Tonic identification
        tonic = self.identify_tonic(pitch)

        # histogram computation
        pitch_distribution = self.compute_pitch_distribution(pitch, tonic)
        pitch_class_distribution = pitch_distribution.to_pcd()

        # makam recognition
        if makam is None:
            raise NotImplementedError('Makam recognition is not integrated.')

        # transposition (ahenk) identification
        ahenk = self.identify_ahenk(tonic, makam)

        # tuning analysis and stable pitch extraction
        stable_notes = self.get_stable_notes(pitch_distribution, tonic, makam)

        # return as a dictionary
        return {'pitch': pitch, 'tonic': tonic, 'ahenk': ahenk, 'makam': makam,
                'pitch_distribution': pitch_distribution,
                'pitch_class_distribution': pitch_class_distribution,
                'stable_notes': stable_notes}

    def extract_pitch(self, filename):
        if self.verbose:
            print("Extracting predominant melody of ", filename)

        results = self._pitchExtractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def identify_tonic(self, pitch):
        if self.verbose:
            print("Identifying tonic from the predominant melody of ",
                  pitch['source'])

        tonic = self._tonicIdentifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        return tonic

    @staticmethod
    def identify_ahenk(tonic, makamstr):
        ahenk = AhenkIdentifier.identify(tonic['value'], makamstr)
        ahenk['source'] = tonic['source']

        return ahenk

    def compute_pitch_distribution(self, pitch, tonic):
        if self.verbose:
            print("Computing pitch distribution of ", pitch['source'])

        return PitchDistribution.from_hz_pitch(
            np.array(pitch['pitch'])[:, 1], ref_freq=tonic['value'],
            smooth_factor=self._pd_params['smooth_factor'],
            step_size=self._pd_params['step_size'])

    def compute_class_pitch_distribution(self, pitch, tonic):
        if self.verbose:
            print("Computing pitch class distribution of ", pitch['source'])

        return self.compute_pitch_distribution(pitch, tonic).to_pcd()

    def get_stable_notes(self, pitch_distribution, tonic, makamstr):
        if self.verbose:
            print("Computing pitch class distribution of ", tonic['source'])

        return self._noteModeler.calculate_notes(pitch_distribution,
                                                 tonic['value'], makamstr)

    def set_pitch_extractor_params(self, **kwargs):
        if any(key not in self._pitchExtractor.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._pitchExtractor.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._pitchExtractor, key, value)

    def set_tonic_identifier_params(self, **kwargs):
        if any(key not in self._tonicIdentifier.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._tonicIdentifier.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._tonicIdentifier, key, value)

    def set_pitch_distibution_params(self, **kwargs):
        if any(key not in self._pd_params.keys() for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._pd_params.keys()))

        for key, value in kwargs.items():
            self._pd_params[key] = value

    def set_note_modeler_params(self, **kwargs):
        if any(key not in self._noteModeler.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._noteModeler.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._noteModeler, key, value)
