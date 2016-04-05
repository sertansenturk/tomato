import numpy as np
from matplotlib import gridspec
import matplotlib.pyplot as plt

from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer


class Plotter(object):
    @staticmethod
    def plot_audio_features(pitch=None, pitch_distribution=None, notes=None,
                            note_models=None, melodic_progression=None,):
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

        # plot performed notes
        if notes is not None:
            Plotter._plot_performed_notes(ax1, notes)

        # plot pitch distribution to the second subplot
        ax2.plot(pitch_distribution.vals, pitch_distribution.bins)

        # note models
        ytick_vals = Plotter._plot_note_models(
            ax2, note_models, pitch_distribution)

        # plot melodic progression
        AudioSeyirAnalyzer.plot(melodic_progression, ax3)

        # ylabel
        ax1.set_ylabel('Frequency (Hz)')
        ax3.set_ylabel('')  # remove the automatically given ylabel (frequency)

        # set time xticks
        if pitch[-1, 0] > 60:
            xtick_vals = np.arange(pitch[0, 0], pitch[-1, 0], 30)  # 30 sec
            ax3.set_xticks(xtick_vals)

        # define xlim higher than the highest peak so the note names have space
        ax2.set_xlim([0, 1.2 * max(pitch_distribution.vals)])

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
        ax3.set_ylim([np.min(pitch_distribution.bins),
                      np.max(pitch_distribution.bins)])

        # remove the spines from the third subplot
        ax3.spines['bottom'].set_visible(False)
        ax3.spines['left'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.get_yaxis().set_ticks([])

        return fig, (ax1, ax2, ax3)

    @staticmethod
    def _plot_note_models(ax2, note_models, pitch_distribution):
        max_rel_occur = Plotter._get_relative_note_occurences(
            note_models, pitch_distribution)

        Plotter._plot_note_distributions(ax2, note_models)

        ytick_vals = Plotter._plot_stable_pitches(
            ax2, max_rel_occur, note_models, max(pitch_distribution.vals))

        return ytick_vals

    @staticmethod
    def _plot_stable_pitches(ax, max_rel_occur, note_models, max_pd_height):
        ytick_vals = []
        for note_symbol, note in note_models.iteritems():
            if note['rel_occur'] > max_rel_occur * 0.1:
                ytick_vals.append(note['stable_pitch']['value'])

                # plot the performed frequency as a dashed line
                ax.hlines(y=note['theoretical_pitch']['value'], xmin=0,
                          xmax=note['rel_occur'], linestyles='dashed')

                # mark notes
                if note['performed_interval']['value'] == 0.0:  # tonic
                    ax.plot(note['rel_occur'], note['stable_pitch']['value'],
                            'cD', ms=10)
                else:
                    ax.plot(note['rel_occur'], note['stable_pitch']['value'],
                            'cD', ms=6, c='r')

                # print note name, lift the text a little bit
                txt_x_val = (note['rel_occur'] + 0.03 * max_pd_height)
                txt_str = ', '.join(
                    [note_symbol,
                     str(int(round(note['performed_interval']['value']))) +
                     ' cents'])
                ax.text(txt_x_val, note['stable_pitch']['value'], txt_str,
                        style='italic', horizontalalignment='left',
                        verticalalignment='center')
        return ytick_vals

    @staticmethod
    def _get_relative_note_occurences(note_models, pitch_distribution):
        max_rel_occur = 0
        for note_symbol, note in note_models.iteritems():
            # get the relative occurence of each note from the pitch
            # distribution
            dists = np.array([abs(note['stable_pitch']['value'] - dist_bin)
                              for dist_bin in pitch_distribution.bins])
            peak_ind = np.argmin(dists)
            note['rel_occur'] = pitch_distribution.vals[peak_ind]
            max_rel_occur = max([max_rel_occur, note['rel_occur']])
        return max_rel_occur

    @staticmethod
    def _plot_note_distributions(ax, note_models):
        for note_symbol, note in note_models.iteritems():
            try:
                ax.plot(note_models[note_symbol]['distribution'].vals,
                        note_models[note_symbol]['distribution'].bins,
                        label=note_symbol)
            except KeyError:
                pass  # note model is not available

    @staticmethod
    def _plot_performed_notes(ax, notes):
        for note in notes:
            ax.plot(note['interval'], [note['performedPitch']['value'],
                                       note['performedPitch']['value']],
                    'r', alpha=0.4, linewidth=4)
