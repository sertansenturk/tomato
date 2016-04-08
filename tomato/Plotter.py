import numpy as np
from matplotlib import gridspec
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer


class Plotter(object):
    @staticmethod
    def plot_audio_features(pitch=None, pitch_distribution=None,
                            sections=None, notes=None, note_models=None,
                            melodic_progression=None):
        # create the figure with four subplots with different size
        # first is for the predominant melody
        # second is the pitch distribution, it shares the y axis with the first
        # third is the melodic progression, it shares the x axis with the first
        # fourth is for the sections, it is on top the third
        fig = plt.figure()
        gs = gridspec.GridSpec(2, 2, width_ratios=[6, 1], height_ratios=[4, 1])

        ax1 = fig.add_subplot(gs[0])  # pitch and notes
        ax2 = fig.add_subplot(gs[1], sharey=ax1)  # pitch dist. and note models
        ax4 = fig.add_subplot(gs[2])  # sections
        ax3 = plt.twiny(ax4)  # melodic progression
        ax1.get_shared_x_axes().join(ax1, ax3)
        fig.subplots_adjust(hspace=0, wspace=0)

        # plot pitch track
        ax1.plot(pitch[:, 0], pitch[:, 1], 'g', label='Pitch', alpha=0.7)

        ax1.xaxis.set_label_coords(0.5, 0.05)
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Frequency (Hz)')

        # move x-axis of ax1 and ax3 in between, e.g. top of ax1
        ax1.tick_params(axis='x', pad=-15)
        ax1.xaxis.set_label_position('top')

        # plot performed notes
        if notes is not None:
            Plotter._plot_performed_notes(ax1, notes)

        # plot pitch distribution to the second subplot
        ax2.plot(pitch_distribution.vals, pitch_distribution.bins,
                 color='gray')
        plt.setp(ax2.get_yticklabels(), visible=False)

        # note models
        if note_models is not None:
            ytick_vals = Plotter._plot_note_models(
                ax2, note_models, pitch_distribution)
        else:
            peak_idx = pitch_distribution.detect_peaks()[0]
            ytick_vals = pitch_distribution.bins[peak_idx]

        # set the frequency ticks and grids
        ax1.set_yticks(ytick_vals)
        ax1.yaxis.grid(True)

        ax2.set_yticks(ytick_vals)
        ax2.yaxis.grid(True)

        # remove spines from the second subplot
        ax2.spines['top'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # define xlim higher than the highest peak so the note names have space
        ax2.set_xlim([0, 1.2 * max(pitch_distribution.vals)])

        # remove the axis of the subplot 2
        ax2.axis('off')

        # plot melodic progression
        AudioSeyirAnalyzer.plot(melodic_progression, ax3)
        ax3.set_xlabel('')  # remove the automatically given labels
        ax3.set_ylabel('')
        plt.setp(ax3.get_yticklabels(), visible=False)
        plt.setp(ax3.get_xticklabels(), visible=False)

        # set xlim to the last time in the pitch track
        ax3.set_xlim([pitch[0, 0], pitch[-1, 0]])
        ax3.set_ylim([np.min(pitch_distribution.bins),
                      np.max(pitch_distribution.bins)])

        # remove the spines from the third subplot
        ax3.spines['bottom'].set_visible(False)
        ax3.spines['left'].set_visible(False)
        ax3.spines['right'].set_visible(False)
        ax3.get_yaxis().set_ticks([])

        # plot sections
        sec_labels = []
        sec_locs = []
        for sec in sections:
            # get the time interval
            tt = sec['time']
            dur = tt[1] - tt[0]

            # get the plot limits
            ylim = ax3.get_ylim()

            # create the rectangle
            p = patches.Rectangle((tt[0], ylim[0]), dur, ylim[1], alpha=0.3)
            ax4.add_patch(p)

            sec_labels.append(sec['name'])
            sec_locs.append(np.mean(tt))

        plt.setp(ax4.get_yticklabels(), visible=False)

        # section labels
        ax4.set_xticks(sec_locs)
        ax4.set_xticklabels(sec_labels, rotation=-15)

        ax4.set_xlim(ax1.get_xlim())

        return fig, (ax1, ax2, ax3, ax4)

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
            ax.plot(note['interval'], [note['performed_pitch']['value'],
                                       note['performed_pitch']['value']],
                    'r', alpha=0.4, linewidth=4)
