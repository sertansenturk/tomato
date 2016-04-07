import json
from scipy.io import savemat
import cStringIO
import tempfile
import numpy as np
from copy import deepcopy
import warnings

from alignedpitchfilter.AlignedPitchFilter import AlignedPitchFilter
from alignednotemodel.AlignedNoteModel import AlignedNoteModel

from tomato.MCRCaller import MCRCaller
from tomato.IO import IO
from tomato.ParamSetter import ParamSetter
from tomato.Plotter import Plotter

# instantiate a mcr_caller
_mcr_caller = MCRCaller()


class JointAnalyzer(ParamSetter):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # extractors
        self._tonicTempoExtractor = _mcr_caller.get_binary_path(
            'extractTonicTempoTuning')
        self._audioScoreAligner = _mcr_caller.get_binary_path(
            'alignAudioScore')
        self._alignedPitchFilter = AlignedPitchFilter()
        self._alignedNoteModel = AlignedNoteModel()

    def analyze(self, score_filename='', score_data=None,
                audio_filename='', audio_pitch=None):
        # joint score-informed tonic identification and tempo estimation
        try:
            tonic, tempo = self.extract_tonic_tempo(
                score_filename, score_data, audio_filename, audio_pitch)
        except RuntimeError as e:
            warnings.warn(e.message, RuntimeWarning)
            joint_features = None
            audio_features = None
            return joint_features, audio_features

        # section linking and note-level alignment
        try:
            sections, notes, section_candidates = self.align_audio_score(
                score_filename, score_data,
                audio_filename, audio_pitch, tonic, tempo)
        except RuntimeError as e:
            warnings.warn(e.message, RuntimeWarning)
            joint_features = None
            audio_features = {'tonic': tonic, 'tempo': tempo}
            return joint_features, audio_features

        # aligned pitch filter
        aligned_pitch, aligned_notes = self.filter_pitch(audio_pitch, notes)

        # aligned note model
        note_models, pitch_distribution, aligned_tonic = self.get_note_models(
            aligned_pitch, notes, tonic['symbol'])

        joint_features = {'sections': sections, 'notes': aligned_notes,
                          'note_models': note_models}
        audio_features = {'pitch': aligned_pitch, 'tonic': aligned_tonic,
                          'tempo': tempo}

        return joint_features, audio_features

    @staticmethod
    def summarize(audio_features=None, score_features=None,
                  joint_features=None, score_informed_audio_features=None):
        # initialize
        sdict = {'audio': {}, 'score': score_features, 'joint': {}}

        sdict['audio']['metadata'] = audio_features['metadata']
        if score_informed_audio_features is not None:
            sdict['audio']['pitch'] = score_informed_audio_features['pitch']
            sdict['audio']['tonic'] = score_informed_audio_features['tonic']
            sdict['audio']['tempo'] = score_informed_audio_features['tempo']
            sdict['audio']['melodic_progression'] = \
                score_informed_audio_features['melodic_progression']
            sdict['audio']['transposition'] = score_informed_audio_features[
                'transposition']
            sdict['audio']['pitch_distribution'] = \
                score_informed_audio_features['pitch_distribution']
            sdict['audio']['pitch_class_distribution'] = \
                score_informed_audio_features['pitch_class_distribution']
        else:
            sdict['audio']['pitch'] = audio_features['pitch_filtered']
            sdict['audio']['tonic'] = audio_features['tonic']
            sdict['audio']['melodic_progression'] = audio_features[
                'melodic_progression']
            sdict['audio']['transposition'] = audio_features['transposition']
            sdict['audio']['pitch_distribution'] = \
                audio_features['pitch_distribution']
            sdict['audio']['pitch_class_distribution'] = \
                audio_features['pitch_class_distribution']
            # only add stable_notes if the joint features, hence the note
            # models are not given
            sdict['audio']['stable_notes'] = audio_features['stable_notes']

        if score_features is not None:
            sdict['audio']['makam'] = score_features['makam']['symbtr_slug']
        else:
            sdict['audio']['makam'] = audio_features['makam']

        # accumulate joint dict
        if joint_features is not None:
            sdict['joint']['sections'] = joint_features['sections']
            sdict['joint']['notes'] = joint_features['notes']
            sdict['joint']['note_models'] = joint_features['note_models']

        return sdict

    def extract_tonic_tempo(self, score_filename='', score_data=None,
                            audio_filename='', audio_pitch=None):
        if self.verbose:
            print("- Extracting score-informed tonic and tempo of " +
                  audio_filename)

        # create the temporary input and output files wanted by the binary
        temp_score_data_file = IO.create_temp_file(
            '.json', json.dumps(score_data))

        # matlab
        matout = cStringIO.StringIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = IO.create_temp_file(
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
            IO.remove_temp_files(
                temp_score_data_file, temp_pitch_file, temp_out_folder)
            raise RuntimeError("Score-informed tonic, tonic and tuning "
                               "extraction is not successful. Please "
                               "check the error in the terminal.")

        out_dict = IO.load_json_from_temp_folder(
            temp_out_folder, ['tempo', 'tonic', 'tuning'])

        # unlink the temporary files
        IO.remove_temp_files(
            temp_score_data_file, temp_pitch_file, temp_out_folder)

        # tidy outouts
        # We omit the tuning output in the binary because
        # get_aligned_note_models is more informative
        procedure = 'Score informed joint tonic and tempo extraction'

        tonic = out_dict['tonic']['scoreInformed']
        tonic = IO.dict_keys_to_snake_case(tonic)
        tonic['procedure'] = procedure
        tonic['source'] = audio_filename

        tempo = out_dict['tempo']['scoreInformed']
        tempo['average'] = IO.dict_keys_to_snake_case(tempo['average'])
        tempo['average']['procedure'] = procedure
        tempo['average']['source'] = audio_filename
        tempo['average'].pop("method", None)

        tempo['relative'] = IO.dict_keys_to_snake_case(
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
        temp_score_data_file = IO.create_temp_file(
            '.json', json.dumps(score_data))

        # tonic has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tonic_ = IO.dict_keys_to_camel_case(audio_tonic)
        temp_tonic_file = IO.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tonic_}))

        # tempo has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tempo_ = deepcopy(audio_tempo)
        audio_tempo_['relative'] = IO.dict_keys_to_camel_case(
            audio_tempo['relative'])
        audio_tempo_['average'] = IO.dict_keys_to_camel_case(
            audio_tempo['average'])
        temp_tempo_file = IO.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tempo_}))

        # matlab
        matout = cStringIO.StringIO()
        savemat(matout, audio_pitch)

        temp_pitch_file = IO.create_temp_file(
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
            IO.remove_temp_files(
                temp_score_data_file, temp_tonic_file, temp_tempo_file,
                temp_pitch_file, temp_out_folder)
            raise RuntimeError("Audio score alignment is not successful. "
                               "Please check the error in the terminal.")

        out_dict = IO.load_json_from_temp_folder(
            temp_out_folder, ['sectionLinks', 'alignedNotes'])

        # unlink the temporary files
        IO.remove_temp_files(temp_score_data_file, temp_tonic_file,
                             temp_tempo_file, temp_pitch_file, temp_out_folder)

        notes = [IO.dict_keys_to_snake_case(n)
                 for n in out_dict['alignedNotes']['notes']]

        return (out_dict['sectionLinks']['links'], notes,
                out_dict['sectionLinks']['candidates'])

    def filter_pitch(self, pitch, aligned_notes):
        if self.verbose:
            print("- Filtering predominant melody of %s after audio-score "
                  "alignment." % (pitch['source']))
        aligned_notes_ = [IO.dict_keys_to_camel_case(n)
                          for n in deepcopy(aligned_notes)]

        pitch_temp, notes_filtered, synth_pitch = \
            self._alignedPitchFilter.filter(pitch['pitch'], aligned_notes_)

        notes_filtered = [IO.dict_keys_to_snake_case(n)
                          for n in notes_filtered]

        pitch_filtered = deepcopy(pitch)
        pitch_filtered['pitch'] = pitch_temp
        pitch_filtered['citation'] = 'SenturkThesis'
        pitch_filtered['procedure'] = 'Pitch filtering according to ' \
                                      'audio-score alignment'

        return pitch_filtered, notes_filtered

    def get_note_models(self, pitch, aligned_notes, tonic_symbol):
        if self.verbose:
            print("- Computing the note models for " + pitch['source'])

        aligned_notes_ = [IO.dict_keys_to_camel_case(n)
                          for n in deepcopy(aligned_notes)]

        note_models, pitch_distibution, tonic = self._alignedNoteModel.\
            get_models(pitch['pitch'], aligned_notes_, tonic_symbol)

        for note in note_models.keys():
            note_models[note] = IO.dict_keys_to_snake_case(
                note_models[note])

        tonic = IO.dict_keys_to_snake_case(tonic['alignment'])
        tonic['source'] = pitch['source']

        return note_models, pitch_distibution, tonic

    def set_tonic_tempo_extractor_params(self, **kwargs):
        raise NotImplementedError

    def set_audio_score_aligner_params(self, **kwargs):
        raise NotImplementedError

    def set_pitch_filter_params(self, **kwargs):
        self._set_params('_alignedPitchFilter', **kwargs)

    def set_note_model_params(self, **kwargs):
        self._set_params('_alignedNoteModel', **kwargs)

    @staticmethod
    def plot(summarized_features):
        pitch = np.array(deepcopy(
            summarized_features['audio']['pitch']['pitch']))
        pitch[pitch[:, 1] < 20.0, 1] = np.nan  # remove inaudible for plots

        pitch_distribution = deepcopy(
            summarized_features['audio']['pitch_distribution'])

        try:  # convert the bins to hz, if they are given in cents
            pitch_distribution.cent_to_hz()
        except ValueError:
            pass

        try:
            note_models = deepcopy(summarized_features['joint']['note_models'])
        except KeyError:  # note_models is not computed
            note_models = deepcopy(
                summarized_features['audio']['stable_notes'])

        melodic_progression = deepcopy(
            summarized_features['audio']['melodic_progression'])

        try:
            aligned_notes = deepcopy(summarized_features['joint']['notes'])
        except KeyError:  # audio score alignment failed
            aligned_notes = None

        return Plotter.plot_audio_features(
            pitch=pitch, pitch_distribution=pitch_distribution,
            notes=aligned_notes, note_models=note_models,
            melodic_progression=melodic_progression)
