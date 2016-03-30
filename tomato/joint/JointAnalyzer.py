import json
from scipy.io import savemat
import cStringIO
# import pickle
import os
from copy import deepcopy
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

    def extract_tonic_tempo_tuning(self, score_filename, score_data,
                                   audio_filename, pitch):
        if self.verbose:
            print("- Extracting score-informed tonic, tonic and tuning " +
                  audio_filename)

        # create the temporary input and output files wanted by the binary
        pitch_ = deepcopy(pitch)
        pitch_['pitch'] = pitch_['pitch'].tolist()  # required to save as mat

        import pdb
        pdb.set_trace()
        _tt = savemat(cStringIO.StringIO(), pitch_)

        temp_score_data_file = _mcr_caller.create_temp_file(
            '.json', json.dumps(score_data))
        temp_pitch_file = _mcr_caller.create_temp_file(
            '.mat', savemat(cStringIO.StringIO(), pitch_))

        temp_out_file = _mcr_caller.create_temp_file('.json', '')

        # call the binary
        callstr = ["extractTonicTempoTuning %s %s %s %s %s" %
                   (score_filename, temp_score_data_file, audio_filename,
                    temp_pitch_file, temp_out_file)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        import pdb
        pdb.set_trace()
        if "segmentation complete!" not in out:
            os.unlink(temp_score_data_file)  # unlink the temporary files
            os.unlink(temp_pitch_file)
            os.unlink(temp_out_file)
            raise IOError("Score-informed tonic, tonic and tuning "
                          "extraction is not successful. Please "
                          "check and report the error in the terminal.")

        # load the results from the temporary file
        tonic_tempo_tuning = json.load(open(temp_out_file))

        # unlink the temporary files
        os.unlink(temp_score_data_file)
        os.unlink(temp_pitch_file)
        os.unlink(temp_out_file)

        return tonic_tempo_tuning

    def align_audio_score(self):
        pass
