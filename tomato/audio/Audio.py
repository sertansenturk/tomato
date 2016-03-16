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
        self.melodyExtractor = PredominantMelodyMakam()

    def extract_pitch(self):
        results = self.melodyExtractor.run(self.filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch
