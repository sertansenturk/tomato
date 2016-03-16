from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam
from tonicidentifier.TonicLastNote import TonicLastNote
from ahenkidentifier.AhenkIdentifier import AhenkIdentifier


class AudioAnalyzer(object):
    '''

    '''
    def __init__(self, verbose=False):
        '''

        :return:
        '''
        self.verbose = verbose

        # extractors
        self._pitchExtractor = PredominantMelodyMakam()
        self._tonicIdentifier = TonicLastNote()

    def extract_pitch(self, filename):
        '''

        :return:
        '''
        if self.verbose:
            print("Extracting predominant melody of ", filename)

        results = self._pitchExtractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def identify_tonic(self, pitch):
        '''

        :param pitch:
        :return:
        '''
        if self.verbose:
            print("Identifying tonic from the predominant melody of ",
                  pitch['source'])

        tonic = self._tonicIdentifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        return tonic

    def identify_ahenk(self, tonic, makamstr):
        '''

        :param tonic:
        :param makam:
        :return:
        '''
        ahenk = AhenkIdentifier.identify(tonic['value'], makamstr)
        ahenk['source'] = tonic['source']

        return ahenk

    def set_pitch_extractor_params(self, **kwargs):
        '''

        :param kwargs:
        :return:
        '''
        for key, value in kwargs.items():
            setattr(self._pitchExtractor, key, value)

    def set_tonic_identifier_params(self, **kwargs):
        '''

        :param kwargs:
        :return:
        '''
        for key, value in kwargs.items():
            setattr(self._tonicIdentifier, key, value)
