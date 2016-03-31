import json
from scipy.io import savemat
import cStringIO
import tempfile
# import pickle
import os
from copy import deepcopy
from tomato.MCRCaller import MCRCaller
from alignedpitchfilter.AlignedPitchFilter import AlignedPitchFilter

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class JointAnalyzer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._tonicTempoExtractor = _mcr_caller.get_binary_path(
            'extractTonicTempoTuning')
        self._audioScoreAligner = _mcr_caller.get_binary_path(
            'alignAudioScore')
        self._alignedPitchFilter = AlignedPitchFilter()

    def extract_tonic_tempo(self, score_filename='', score_data=None,
                            audio_filename='', audio_pitch=None):
        if self.verbose:
            print("- Extracting score-informed tonic and tempo of " +
                  audio_filename)

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = _mcr_caller.create_temp_file(
            '.json', json.dumps(score_data))

        # matlab
        matout = cStringIO.StringIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = _mcr_caller.create_temp_file(
            '.mat', matout.getvalue())

        temp_out_folder = tempfile.mkdtemp()

        # call the binary
        callstr = ["%s %s %s %s %s %s" %
                   (self._tonicTempoExtractor, score_filename,
                    temp_score_data_file, audio_filename, temp_pitch_file,
                    temp_out_folder)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        if "Tonic-Tempo-Tuning Extraction took" not in out:
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
        tonic = _mcr_caller.lower_key_first_letter(tonic)
        tonic['procedure'] = procedure
        tonic['source'] = audio_filename

        tempo = out_dict['tempo']['scoreInformed']
        tempo['average'] = _mcr_caller.lower_key_first_letter(tempo['average'])
        tempo['average']['procedure'] = procedure
        tempo['average']['source'] = audio_filename
        tempo['average'].pop("method", None)

        tempo['relative'] = _mcr_caller.lower_key_first_letter(
            tempo['relative'])
        tempo['relative']['procedure'] = procedure
        tempo['relative']['source'] = audio_filename
        tempo['relative'].pop("method", None)

        return tonic, tempo

    def align_audio_score(self, score_filename='', score_data=None,
                          audio_filename='', audio_pitch=None,
                          audio_tonic=None, audio_tempo=None):
        if self.verbose:
            print("- Aligning audio recording %s and music score %s."
                  % (audio_filename, score_filename))

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = _mcr_caller.create_temp_file(
            '.json', json.dumps(score_data))

        # tonic has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tonic_ = _mcr_caller.upper_key_first_letter(audio_tonic)
        temp_tonic_file = _mcr_caller.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tonic_}))

        # tempo has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tempo_ = deepcopy(audio_tempo)
        audio_tempo_['relative'] = _mcr_caller.upper_key_first_letter(
            audio_tempo['relative'])
        audio_tempo_['average'] = _mcr_caller.upper_key_first_letter(
            audio_tempo['average'])
        temp_tempo_file = _mcr_caller.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tempo_}))

        # matlab
        matout = cStringIO.StringIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = _mcr_caller.create_temp_file(
            '.mat', matout.getvalue())

        temp_out_folder = tempfile.mkdtemp()

        # call the binary
        callstr = ["%s %s %s '' %s %s %s %s '' %s" %
                   (self._audioScoreAligner, score_filename,
                    temp_score_data_file, audio_filename, temp_pitch_file,
                    temp_tonic_file, temp_tempo_file, temp_out_folder)]

        out, err = _mcr_caller.call(callstr)

        # check the MATLAB output
        if "Audio-score alignment took" not in out:
            os.unlink(temp_score_data_file)  # unlink the temporary files
            os.unlink(temp_tonic_file)
            os.unlink(temp_tempo_file)
            os.unlink(temp_pitch_file)
            os.rmdir(temp_out_folder)
            raise IOError("Audio score alignment is not successful. Please "
                          "check and report the error in the terminal.")

        out_dict = _mcr_caller.load_json_from_temp_folder(
            temp_out_folder, ['sectionLinks', 'alignedNotes'])

        # unlink the temporary files
        os.unlink(temp_score_data_file)
        os.unlink(temp_tonic_file)
        os.unlink(temp_tempo_file)
        os.unlink(temp_pitch_file)
        os.rmdir(temp_out_folder)

        section_links = out_dict['sectionLinks']['links']
        section_candidates = out_dict['sectionLinks']['candidates']
        aligned_notes = out_dict['alignedNotes']['notes']

        return section_links, aligned_notes, section_candidates

    def filter_pitch(self, pitch, aligned_notes):
        if self.verbose:
            print("- Filtering predominant melody of %s after audio-score "
                  "alignment." % (pitch['source']))

        pitch_temp, notes_filtered, synth_pitch = \
            self._alignedPitchFilter.filter(pitch['pitch'], aligned_notes)

        pitch_filtered = deepcopy(pitch)
        pitch_filtered['pitch'] = pitch_temp

        return pitch_filtered, notes_filtered

    def set_pitch_filter_params(self, **kwargs):
        if any(key not in self._alignedPitchFilter.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._alignedPitchFilter.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._alignedPitchFilter, key, value)
