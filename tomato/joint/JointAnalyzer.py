import json
from scipy.io import savemat
import cStringIO
import tempfile
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

    def extract_tonic_tempo(self, score_filename, score_data,
                            audio_filename, audio_pitch):
        if self.verbose:
            print("- Extracting score-informed tonic and tempo" +
                  audio_filename)

        audio_pitch_ = deepcopy(audio_pitch)
        audio_pitch_['pitch'] = audio_pitch_['pitch'].tolist()

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = _mcr_caller.create_temp_file(
            '.json', json.dumps(score_data))

        # matlab
        matout = cStringIO.StringIO()
        savemat(matout, audio_pitch_)

        temp_pitch_file = _mcr_caller.create_temp_file(
            '.mat', matout.getvalue())

        temp_out_folder = tempfile.mkdtemp()

        # call the binary
        callstr = ["%s %s %s %s %s %s" %
                   (self._tonic_tempo_tuning_extractor, score_filename,
                    temp_score_data_file, audio_filename, temp_pitch_file,
                    temp_out_folder)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        if "Tonic-Tempo-Tuning Extraction took" not in out:
            import pdb
            pdb.set_trace()
            os.unlink(temp_score_data_file)  # unlink the temporary files
            os.unlink(temp_pitch_file)
            os.rmdir(temp_out_folder)
            raise IOError("Score-informed tonic, tonic and tuning "
                          "extraction is not successful. Please "
                          "check and report the error in the terminal.")

        out_dict = _mcr_caller.load_json_from_temp_folder(
            temp_out_folder, ['tempo', 'tonic', 'tuning'])

        # unlink the temporary files
        os.unlink(temp_score_data_file)
        os.unlink(temp_pitch_file)
        os.rmdir(temp_out_folder)

        # tidy outouts
        # We omit the tuning output in the binary because
        # get_aligned_note_models is more informative
        procedure = 'Score informed joint tonic and tempo extraction'

        tonic = out_dict['tonic']['scoreInformed']
        tonic = dict((k[:1].lower() + k[1:], v) for k, v in tonic.iteritems())
        tonic['procedure'] = procedure
        tonic['source'] = audio_filename

        tempo = out_dict['tempo']['scoreInformed']
        tempo['average'] = dict((k[:1].lower() + k[1:], v)
                                for k, v in tempo['average'].iteritems())
        tempo['average']['procedure'] = procedure
        tempo['average']['source'] = audio_filename
        tempo['average'].pop("method", None)

        tempo['relative'] = dict((k[:1].lower() + k[1:], v)
                                 for k, v in tempo['relative'].iteritems())
        tempo['relative']['procedure'] = procedure
        tempo['relative']['source'] = audio_filename
        tempo['relative'].pop("method", None)

        return tonic, tempo

    def align_audio_score(self):
        pass
