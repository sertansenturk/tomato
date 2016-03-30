# import json
# import pickle
import os
# import tempfile

from tomato.MCRCaller import MCRCaller

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class JointAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._tonic_tempo_tuning_extractor = _mcr_caller.get_binary_path(
            'extractTonicTempoTuning')
        self._audio_score_aligner = _mcr_caller.get_binary_path(
            'alignAudioScore')

    def extract_tonic_tempo_tuning(self):
        pass

    def align_audio_score(self):
        pass
