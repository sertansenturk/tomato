from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam


class Audio(object):
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

    def extract_pitch(self):
        '''

        :return:
        '''
        results = self._melodyExtractor.run(self.filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def set_pitch_extractor_params(self, **kwargs):
        '''

        :param kwargs:
        :return:
        '''
        for key, value in kwargs.items():
            setattr(self._melodyExtractor, key, value)
