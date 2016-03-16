from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam
from tonicidentifier.TonicLastNote import TonicLastNote


class AudioAnalyzer(object):
    '''

    '''
    def __init__(self, filename, verbose=False):
        '''

        :return:
        '''
        self.filename = filename
        self.verbose = verbose

        # extractors
        self._melodyExtractor = PredominantMelodyMakam()
        self._tonic_identifier = TonicLastNote()

    def extract_pitch(self):
        '''

        :return:
        '''
        results = self._melodyExtractor.run(self.filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def identify_tonic(self, pitch):
        tonic, pitch, pitch_chunks, pitch_distribution, stable_pitches = \
            self._tonic_identifier.identify(pitch)

        return tonic

    def set_pitch_extractor_params(self, **kwargs):
        '''

        :param kwargs:
        :return:
        '''
        for key, value in kwargs.items():
            setattr(self._melodyExtractor, key, value)
