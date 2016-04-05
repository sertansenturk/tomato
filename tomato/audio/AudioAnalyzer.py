import numpy as np
from copy import deepcopy
from matplotlib import gridspec
import matplotlib.pyplot as plt

from predominantmelodymakam.PredominantMelodyMakam import \
    PredominantMelodyMakam
from pitchfilter.PitchFilter import PitchFilter
from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer
from tonicidentifier.TonicLastNote import TonicLastNote
from ahenkidentifier.AhenkIdentifier import AhenkIdentifier
from notemodel.NoteModel import NoteModel
from modetonicestimation.PitchDistribution import PitchDistribution

from tomato.ParamSetter import ParamSetter


class AudioAnalyzer(ParamSetter):
    def __init__(self, verbose=False):
        self.verbose = verbose

        # settings that are not defined in the respective classes
        self._pd_params = {'kernel_width': 7.5, 'step_size': 7.5}
        # - for melodic progression None means, applying the rule of thumb
        #   defined in the method "get_melodic_progression". This class has
        #   two parameters defined in init and the other two defined in the
        #   method call. Here we only store the ones called in the method call.
        self._mel_prog_params = {'frame_dur': None, 'hop_ratio': 0.5,
                                 'min_num_frames': 40, 'max_frame_dur': 30}

        # extractors
        self._pitchExtractor = PredominantMelodyMakam(filter_pitch=False)
        self._pitchFilter = PitchFilter()
        self._melodicProgressionAnalyzer = AudioSeyirAnalyzer()
        self._tonicIdentifier = TonicLastNote()
        self._noteModeler = NoteModel()

    def analyze(self, filepath, makam=None):
        # predominant melody extraction
        pitch = self.extract_pitch(filepath)

        # pitch filtering
        pitch_filtered = self.filter_pitch(pitch)

        # get the melodic prograssion model
        melodic_progression = self.get_melodic_progression(pitch_filtered)

        # tonic identification
        tonic = self.identify_tonic(pitch_filtered)

        # histogram computation
        pitch_distribution = self.compute_pitch_distribution(
            pitch_filtered, tonic)
        pitch_distribution.cent_to_hz()
        pitch_class_distribution = pitch_distribution.to_pcd()

        # makam recognition
        if makam is None:
            raise NotImplementedError('Makam recognition is not integrated.')

        # transposition (ahenk) identification
        transposition = self.identify_transposition(tonic, makam)

        # tuning analysis and stable pitch extraction
        stable_notes = self.get_stable_notes(pitch_distribution, tonic, makam)

        # return as a dictionary
        return {'pitch': pitch, 'pitch_filtered': pitch_filtered,
                'tonic': tonic, 'transposition': transposition, 'makam': makam,
                'melodic_progression': melodic_progression,
                'pitch_distribution': pitch_distribution,
                'pitch_class_distribution': pitch_class_distribution,
                'stable_notes': stable_notes}

    def update_analysis(self, audio_features):
        # make a copy of the existing analysis
        updated_audio_features = deepcopy(audio_features)
        pitch = updated_audio_features['pitch']
        tonic = updated_audio_features['tonic']

        # get the melodic progression model
        melodic_progression = self.get_melodic_progression(pitch)

        # histogram computation
        pitch_distribution = self.compute_pitch_distribution(pitch, tonic)
        pitch_distribution.cent_to_hz()
        pitch_class_distribution = pitch_distribution.to_pcd()

        # transposition (ahenk) identification
        transposition = self.identify_transposition(tonic, tonic['symbol'])

        # add/raplace with the computed features
        updated_audio_features['transposition'] = transposition,
        updated_audio_features['melodic_progression'] = melodic_progression
        updated_audio_features['pitch_distribution'] = pitch_distribution
        updated_audio_features['pitch_class_distribution'] =  \
            pitch_class_distribution

        return updated_audio_features

    def extract_pitch(self, filename):
        if self.verbose:
            print("- Extracting predominant melody of " + filename)

        results = self._pitchExtractor.run(filename)
        pitch = results['settings']  # collapse the keys in settings
        pitch['pitch'] = results['pitch']

        return pitch

    def filter_pitch(self, pitch):
        if self.verbose:
            print("- Filtering predominant melody of " + pitch['source'])

        pitch_filt = deepcopy(pitch)
        pitch_filt['pitch'] = self._pitchFilter.run(pitch_filt['pitch'])
        pitch_filt['citation'] = 'Bozkurt, B. (2008). An automatic pitch ' \
                                 'analysis method for Turkish maqam music. ' \
                                 'Journal of New Music Research, 37(1), 1-13.'

        return pitch_filt

    def get_melodic_progression(self, pitch):
        if self.verbose:
            print("- Obtaining the melodic progression model of " +
                  pitch['source'])

        if self._mel_prog_params['frame_dur'] is None:
            # compute number of frames from some simple "rule of thumb"
            duration = pitch['pitch'][-1][0]
            frame_dur = duration / self._mel_prog_params['min_num_frames']
            frame_dur = int(5 * round(float(frame_dur) / 5))  # round to 5sec

            # force to be between 5 and max_frame_dur
            if frame_dur < 5:
                frame_dur = 5
            elif frame_dur > self._mel_prog_params['max_frame_dur']:
                frame_dur = self._mel_prog_params['max_frame_dur']
        else:
            frame_dur = self._mel_prog_params['frame_dur']

        return self._melodicProgressionAnalyzer.analyze(
            pitch['pitch'], frame_dur=frame_dur,
            hop_ratio=self._mel_prog_params['hop_ratio'])

    def identify_tonic(self, pitch):
        if self.verbose:
            print("- Identifying tonic from the predominant melody of " +
                  pitch['source'])

        tonic = self._tonicIdentifier.identify(pitch['pitch'])[0]

        # add the source audio file
        tonic['source'] = pitch['source']

        return tonic

    def identify_transposition(self, tonic, makam_tonic_str):
        if self.verbose:
            print("- Identifying the transposition of " + tonic['source'])
        transposition = AhenkIdentifier.identify(
            tonic['value'], makam_tonic_str)
        transposition['source'] = tonic['source']

        return transposition

    def compute_pitch_distribution(self, pitch, tonic):
        if self.verbose:
            print("- Computing pitch distribution of " + pitch['source'])

        return PitchDistribution.from_hz_pitch(
            np.array(pitch['pitch'])[:, 1], ref_freq=tonic['value'],
            smooth_factor=self._pd_params['kernel_width'],
            step_size=self._pd_params['step_size'])

    def compute_class_pitch_distribution(self, pitch, tonic):
        if self.verbose:
            print("- Computing pitch class distribution of " + pitch['source'])

        return self.compute_pitch_distribution(pitch, tonic).to_pcd()

    def get_stable_notes(self, pitch_distribution, tonic, makamstr):
        if self.verbose:
            print("- Obtaining the stable notes of " + tonic['source'])

        return self._noteModeler.calculate_notes(pitch_distribution,
                                                 tonic['value'], makamstr)

    def set_pitch_extractor_params(self, **kwargs):
        self._set_params('_pitchExtractor', **kwargs)

    def set_pitch_filter_params(self, **kwargs):
        self._set_params('_pitchFilter', **kwargs)

    def set_pitch_distibution_params(self, **kwargs):
        self._set_params('_pd_params', **kwargs)

    def set_tonic_identifier_params(self, **kwargs):
        self._set_params('_tonicIdentifier', **kwargs)

    def set_melody_progression_params(self, **kwargs):
        method_params = self._mel_prog_params.keys()  # imput parameters
        obj_params = self._melodicProgressionAnalyzer.__dict__.keys()
        if any(key not in (method_params + obj_params)
               for key in kwargs.keys()):
            raise KeyError("Possible parameters are: " + ', '.join(
                method_params + obj_params))

        for key, value in kwargs.items():
            if key in method_params:
                self._mel_prog_params[key] = value
            elif key in obj_params:
                setattr(self._melodicProgressionAnalyzer, key, value)
            else:
                raise KeyError("Unexpected key error")

    def set_note_modeler_params(self, **kwargs):
        self._set_params('_noteModeler', **kwargs)

    @staticmethod
    def plot(features):
        pitch = np.array(deepcopy(features['pitch_filtered']['pitch']))
        pitch[pitch[:, 1] < 20.0, 1] = np.nan  # remove inaudible for plots
        pd_copy = deepcopy(features['pitch_distribution'])
        try:  # convert the bins to hz, if they are given in cents
            pd_copy.cent_to_hz()
        except ValueError:
            pass
        stable_notes = deepcopy(features['stable_notes'])

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
        ax2.plot(pd_copy.vals, pd_copy.bins)

        # plot stable pitches to the second subplot
        max_rel_occur = 0
        for note_symbol, note in stable_notes.iteritems():
            # get the relative occurence of each note from the pitch
            # distribution
            dists = np.array([abs(note['stable_pitch']['value'] - dist_bin)
                              for dist_bin in pd_copy.bins])
            peak_ind = np.argmin(dists)
            note['rel_occur'] = pd_copy.vals[peak_ind]
            max_rel_occur = max([max_rel_occur, note['rel_occur']])

        ytick_vals = []
        for note_symbol, note in stable_notes.iteritems():
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
        AudioSeyirAnalyzer.plot(features['melodic_progression'], ax3)

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
