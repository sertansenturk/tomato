import json
from scipy.io import savemat
import cStringIO
import tempfile
import pickle
import numpy as np
from copy import deepcopy
from matplotlib import gridspec
import matplotlib.pyplot as plt

from alignedpitchfilter.AlignedPitchFilter import AlignedPitchFilter
from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer
from alignednotemodel.AlignedNoteModel import AlignedNoteModel

from tomato.MCRCaller import MCRCaller
from tomato.IO import IO

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
        self._alignedNoteModel = AlignedNoteModel()

    def analyze(self, score_filename='', score_data=None,
                audio_filename='', audio_pitch=None):
        # joint score-informed tonic identification and tempo estimation
        tonic, tempo = self.extract_tonic_tempo(score_filename, score_data,
                                                audio_filename, audio_pitch)

        # section linking and note-level alignment
        sections, notes, section_candidates = self.align_audio_score(
            score_filename, score_data,
            audio_filename, audio_pitch, tonic, tempo)

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
        sdict['joint']['sections'] = joint_features['sections']
        sdict['joint']['notes'] = joint_features['notes']
        sdict['joint']['note_models'] = joint_features['note_models']

        return sdict

    @staticmethod
    def to_json(features, filepath=None):
        save_features = deepcopy(features)
        try:
            save_features['pitch']['pitch'] = save_features['pitch'][
                'pitch'].tolist()
        except AttributeError:
            pass  # already converted to list of lists

        if filepath is None:
            return json.dumps(save_features, indent=4)
        else:
            json.dump(save_features, open(filepath, 'w'), indent=4)

    @staticmethod
    def from_json(filepath):
        try:
            return json.load(open(filepath, 'r'))
        except IOError:  # string given
            return json.loads(filepath)

    @staticmethod
    def to_pickle(features, filepath=None):
        if filepath is None:
            return pickle.dumps(features)
        else:
            pickle.dump(features, open(filepath, 'wb'))

    @staticmethod
    def from_pickle(filepath):
        try:
            return pickle.load(open(filepath, 'rb'))
        except IOError:  # string given
            return pickle.loads(filepath)

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
            raise IOError("Score-informed tonic, tonic and tuning "
                          "extraction is not successful. Please "
                          "check and report the error in the terminal.")

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
        tonic = IO.lower_key_first_letter(tonic)
        tonic['procedure'] = procedure
        tonic['source'] = audio_filename

        tempo = out_dict['tempo']['scoreInformed']
        tempo['average'] = IO.lower_key_first_letter(tempo['average'])
        tempo['average']['procedure'] = procedure
        tempo['average']['source'] = audio_filename
        tempo['average'].pop("method", None)

        tempo['relative'] = IO.lower_key_first_letter(
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
        audio_tonic_ = IO.upper_key_first_letter(audio_tonic)
        temp_tonic_file = IO.create_temp_file(
            '.json', json.dumps({'scoreInformed': audio_tonic_}))

        # tempo has to be enclosed in the key 'score_informed' and all the
        # keys have to start with a capital letter
        audio_tempo_ = deepcopy(audio_tempo)
        audio_tempo_['relative'] = IO.upper_key_first_letter(
            audio_tempo['relative'])
        audio_tempo_['average'] = IO.upper_key_first_letter(
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
            raise IOError("Audio score alignment is not successful. Please "
                          "check and report the error in the terminal.")

        out_dict = IO.load_json_from_temp_folder(
            temp_out_folder, ['sectionLinks', 'alignedNotes'])

        # unlink the temporary files
        IO.remove_temp_files(temp_score_data_file, temp_tonic_file,
                             temp_tempo_file, temp_pitch_file, temp_out_folder)

        notes = [IO.lower_key_first_letter(n)
                 for n in out_dict['alignedNotes']['notes']]

        return (out_dict['sectionLinks']['links'], notes,
                out_dict['sectionLinks']['candidates'])

    def filter_pitch(self, pitch, aligned_notes):
        if self.verbose:
            print("- Filtering predominant melody of %s after audio-score "
                  "alignment." % (pitch['source']))
        aligned_notes_ = [IO.upper_key_first_letter(n)
                          for n in deepcopy(aligned_notes)]

        pitch_temp, notes_filtered, synth_pitch = \
            self._alignedPitchFilter.filter(pitch['pitch'], aligned_notes_)

        notes_filtered = [IO.lower_key_first_letter(n)
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

        aligned_notes_ = [IO.upper_key_first_letter(n)
                          for n in deepcopy(aligned_notes)]

        note_models, pitch_distibution, tonic = self._alignedNoteModel.\
            get_models(pitch['pitch'], aligned_notes_, tonic_symbol)

        for note in note_models.keys():
            note_models[note] = IO.lower_key_first_letter(
                note_models[note])

        tonic = IO.lower_key_first_letter(tonic['alignment'])
        tonic['source'] = pitch['source']

        return note_models, pitch_distibution, tonic

    def set_pitch_filter_params(self, **kwargs):
        if any(key not in self._alignedPitchFilter.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._alignedPitchFilter.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._alignedPitchFilter, key, value)

    def set_note_model_params(self, **kwargs):
        if any(key not in self._alignedNoteModel.__dict__.keys()
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                self._alignedNoteModel.__dict__.keys()))

        for key, value in kwargs.items():
            setattr(self._alignedNoteModel, key, value)

    @staticmethod
    def plot(summarized_features):
        pitch = np.array(deepcopy(
            summarized_features['audio']['pitch']['pitch']))
        pitch[pitch[:, 1] < 20.0, 1] = np.nan  # remove inaudible for plots
        pd_copy = summarized_features['audio']['pitch_distribution']
        try:  # convert the bins to hz, if they are given in cents
            pd_copy.cent_to_hz()
        except ValueError:
            pass
        note_models = deepcopy(summarized_features['joint']['note_models'])
        aligned_notes = deepcopy(summarized_features['joint']['notes'])

        # create the figure with four subplots with different size
        # first is for the predominant melody
        # second is the pitch distribution, it shares the y axis with the first
        # third is the melodic progression, it shares the x axis with the first
        # fourth is not used
        fig = plt.figure()
        gs = gridspec.GridSpec(2, 2, width_ratios=[6, 1], height_ratios=[4, 1])
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1], sharey=ax1)
        ax3 = fig.add_subplot(gs[2], sharex=ax1)

        plt.setp(ax1.get_xticklabels(), visible=False)
        plt.setp(ax2.get_yticklabels(), visible=False)
        plt.setp(ax3.get_yticklabels(), visible=False)

        # plot pitch track
        ax1.plot(pitch[:, 0], pitch[:, 1], 'g', label='Pitch', alpha=0.7)
        fig.subplots_adjust(hspace=0, wspace=0)

        # plot pitch distribution to the second subplot
        ax2.plot(pd_copy.vals, pd_copy.bins,
                 '-.', color='#000000', alpha=0.9)

        # plot aligned notes
        for note in aligned_notes:
            ax1.plot(note['interval'], [note['performedPitch']['value'],
                                        note['performedPitch']['value']],
                     'r', alpha=0.4, linewidth=4)

        # plot stable pitches to the second subplot
        max_rel_occur = 0
        for note_symbol, note in note_models.iteritems():
            # get the relative occurence of each note from the pitch
            # distribution
            dists = np.array([abs(note['stable_pitch']['value'] - dist_bin)
                              for dist_bin in pd_copy.bins])
            peak_ind = np.argmin(dists)
            note['rel_occur'] = pd_copy.vals[peak_ind]
            max_rel_occur = max([max_rel_occur, note['rel_occur']])

        for key in note_models.keys():
            ax2.plot(note_models[key]['distribution'].vals,
                     note_models[key]['distribution'].bins, label=key)

        ytick_vals = []
        for note_symbol, note in note_models.iteritems():
            if note['rel_occur'] > max_rel_occur * 0.1:
                ytick_vals.append(note['stable_pitch']['value'])

                # plot the performed frequency as a dashed line
                ax2.hlines(y=note['theoretical_pitch']['value'], xmin=0,
                           xmax=note['rel_occur'], linestyles='dashed')

                # mark notes
                if note['performed_interval']['value'] == 0.0:  # tonic
                    ax2.plot(note['rel_occur'], note['stable_pitch']['value'],
                             'cD', ms=10)
                else:
                    ax2.plot(note['rel_occur'], note['stable_pitch']['value'],
                             'cD', ms=6, c='r')

                # print note name, lift the text a little bit
                txt_x_val = (note['rel_occur'] +
                             0.03 * max(pd_copy.vals))
                txt_str = ', '.join(
                    [note_symbol,
                     str(int(round(note['performed_interval']['value']))) +
                     ' cents'])
                ax2.text(txt_x_val, note['stable_pitch']['value'], txt_str,
                         style='italic', horizontalalignment='left',
                         verticalalignment='center')

        # plot melodic progression
        AudioSeyirAnalyzer.plot(
            summarized_features['audio']['melodic_progression'], ax3)

        # ylabel
        ax1.set_ylabel('Frequency (Hz)')
        ax3.set_ylabel('')  # remove the automatically given ylabel (frequency)

        # set time xticks
        if pitch[-1, 0] > 60:
            xtick_vals = np.arange(pitch[0, 0], pitch[-1, 0], 30)  # 30 sec
            ax3.set_xticks(xtick_vals)

        # define xlim higher than the highest peak so the note names have space
        ax2.set_xlim([0, 1.2 * max(pd_copy.vals)])

        # remove the axis of the subplot 2
        ax2.axis('off')

        # set the frequency ticks and grids
        ax1.xaxis.grid(True)

        ax1.set_yticks(ytick_vals)
        ax1.yaxis.grid(True)

        ax2.set_yticks(ytick_vals)
        ax2.yaxis.grid(True)

        ax3.xaxis.grid(True)

        # remove spines from the second subplot
        ax2.spines['top'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # set xlim to the last time in the pitch track
        ax3.set_xlim([pitch[0, 0], pitch[-1, 0]])
        ax3.set_ylim([np.min(pd_copy.bins),
                      np.max(pd_copy.bins)])

        # remove the spines from the third subplot
        ax3.spines['bottom'].set_visible(False)
        ax3.spines['left'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.get_yaxis().set_ticks([])

        return fig, (ax1, ax2, ax3)
