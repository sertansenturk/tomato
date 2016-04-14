import numpy as np
from six import iteritems
from matplotlib import gridspec
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FixedLocator
from seyiranalyzer.AudioSeyirAnalyzer import AudioSeyirAnalyzer
import copy
import logging
logging.basicConfig(level=logging.INFO)


class Plotter(object):
    @classmethod
    def plot_audio_features(cls, pitch=None, pitch_distribution=None,
                            sections=None, notes=None, note_models=None,
                            melodic_progression=None, makam=None, tonic=None,
                            transposition=None, tempo=None):
        # parse inputs
        p_in = cls._parse_inputs(
            pitch=pitch, pitch_distribution=pitch_distribution,
            sections=sections, notes=notes, note_models=note_models,
            melodic_progression=melodic_progression, makam=makam, tonic=tonic,
            transposition=transposition, tempo=tempo)

        # create the figure and all the subplots with the shared axis specified
        fig, ax1, ax2, ax3, ax4, ax5 = cls._create_figure()

        # plot the pitch track and the performed notes to the first subplot
        cls._subplot_pitch_notes(ax1, notes, pitch)

        # plot the pitch distribution and the note models to the second subplot
        cls._plot_pitch_dist_note_models(ax2, p_in['note_models'],
                                         p_in['pitch_distribution'])

        # plot the melodic progression to the third subplot
        cls._plot_melodic_progression(
            ax3, p_in['melodic_progression'], p_in['pitch'],
            p_in['pitch_distribution'])

        # plot the sections to the third subplot, onto the melodic progression
        cls._plot_sections(ax1, ax3, ax4, p_in['sections'])

        # print the makam, tonic, ahenk and tempo annot. to the third subplot
        cls._plot_annotations(ax5, p_in['makam'], p_in['tonic'],
                              p_in['transposition'], p_in['tempo'])

        return fig, (ax1, ax2, ax3, ax4, ax5)

    @classmethod
    def _parse_inputs(cls, **kwargs):
        pitch = cls._parse_pitch(kwargs['pitch'])
        pitch_distribution = cls._parse_pitch_distribution(
            kwargs['pitch_distribution'])
        sections = copy.deepcopy(kwargs['sections'])
        notes = copy.deepcopy(kwargs['notes'])
        note_models = copy.deepcopy(kwargs['note_models'])
        melodic_progression = copy.deepcopy(kwargs['melodic_progression'])
        makam = cls._parse_makam(kwargs['makam'])
        tonic = copy.deepcopy(kwargs['tonic'])
        transposition = copy.deepcopy(kwargs['transposition'])
        tempo = copy.deepcopy(kwargs['tempo'])
        inputs = {'pitch': pitch, 'pitch_distribution': pitch_distribution,
                  'sections': sections, 'notes': notes, 'tonic': tonic,
                  'transposition': transposition, 'note_models': note_models,
                  'melodic_progression': melodic_progression, 'makam': makam,
                  'tempo': tempo}

        return inputs

    @staticmethod
    def _parse_pitch(pitch_in):
        try:  # dict
            pitch = copy.deepcopy(pitch_in['pitch'])
        except (TypeError, IndexError):  # list or numpy array
            pitch = copy.deepcopy(pitch_in)

        pitch = np.array(pitch) # convert to numpy array
        pitch[pitch[:, 1] < 20.0, 1] = np.nan  # remove inaudible for plots

        return pitch

    @staticmethod
    def _parse_pitch_distribution(pitch_distribution_in):
        pitch_distribution = copy.deepcopy(pitch_distribution_in)

        try:  # convert the bins to hz, if they are given in cents
            pitch_distribution.cent_to_hz()
        except ValueError:
            logging.debug('The pitch distribution should already be in hz')

        return pitch_distribution_in

    @staticmethod
    def _parse_makam(makam_in):
        try:  # use the MusicBrainz attribute name
            makam = makam_in['mb_attribute']
            if not makam:
                raise ValueError('MusicBrainz attribute is empty.')
        except (KeyError, ValueError):
            try:  # attempt to get the name in mu2
                makam = makam_in['mu2_name']
                if not makam:
                    raise ValueError('MusicBrainz attribute is empty.')
            except (KeyError, ValueError):  # use the slug in symbtr name
                makam = makam_in['symbtr_slug']
        except TypeError:  # string
            makam = makam_in
        return makam

    @staticmethod
    def _create_figure():
        # create the figure with four subplots with different size
        # - 1st is for the predominant melody and performed notes
        # - 2nd is the pitch distribution and note models, it shares the y
        # axis with the 1st
        # - 3rd is the melodic progression, it shares the x axis with the 1st
        # - 4th is for the sections, it is on top the 3rd
        fig = plt.figure()
        gs = gridspec.GridSpec(2, 2, width_ratios=[6, 1], height_ratios=[4, 1])
        ax1 = fig.add_subplot(gs[0])  # pitch and notes
        ax2 = fig.add_subplot(gs[1], sharey=ax1)  # pitch dist. and note models
        ax4 = fig.add_subplot(gs[2])  # sections
        ax5 = fig.add_subplot(gs[3])  # makam, tempo, tonic, ahenk annotations
        ax3 = plt.twiny(ax4)  # melodic progression
        ax1.get_shared_x_axes().join(ax1, ax3)
        fig.subplots_adjust(hspace=0, wspace=0)
        return fig, ax1, ax2, ax3, ax4, ax5

    @classmethod
    def _subplot_pitch_notes(cls, ax1, notes, pitch):
        # plot predominant melody
        ax1.plot(pitch[:, 0], pitch[:, 1], 'g', label='Pitch', alpha=0.7)

        # plot performed notes
        if notes is not None:
            cls._plot_performed_notes(ax1, notes)

        # axis style
        ax1.xaxis.set_label_coords(0.5, 0.05)
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Frequency (Hz)')
        ax1.yaxis.grid(True)

        # move x-axis of ax1 and ax3 in between, e.g. top of ax1
        ax1.tick_params(axis='x', pad=-15)
        ax1.xaxis.set_label_position('top')

    @classmethod
    def _plot_pitch_dist_note_models(cls, ax2, note_models,
                                     pitch_distribution):
        # plot pitch distribution
        ax2.plot(pitch_distribution.vals, pitch_distribution.bins,
                 color='gray')

        # plot note models
        if note_models is not None:
            ytick_vals = cls._plot_note_models(
                ax2, note_models, pitch_distribution)
        else:
            peak_idx = pitch_distribution.detect_peaks()[0]
            ytick_vals = pitch_distribution.bins[peak_idx]

        # set the frequency ticks and grids
        ax2.set_yticks(ytick_vals)
        plt.setp(ax2.get_yticklabels(), visible=False)
        # ax2.yaxis.grid(True)

        # define xlim higher than the highest peak so the note names have space
        ax2.set_xlim([0, 1.2 * max(pitch_distribution.vals)])

        # remove spines from the second subplot
        ax2.spines['top'].set_visible(False)
        ax2.spines['bottom'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_visible(False)

        # remove the axis of the subplot 2
        ax2.axis('off')

    @staticmethod
    def _plot_melodic_progression(ax3, melodic_progression, pitch,
                                  pitch_distribution):
        # plot...
        AudioSeyirAnalyzer.plot(melodic_progression, ax3)

        # axis style
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

    @staticmethod
    def _plot_sections(ax1, ax3, ax4, sections):
        if sections is not None:
            sec_labels = []
            sec_locs = []
            xgrid_locs = []

            unique_sections = list(set(s['name'] for s in sections))
            cmap = plt.get_cmap('gist_rainbow')
            colors = [cmap(i) for i in np.linspace(0, 1, len(unique_sections))]

            for sec in sections:
                # get the time interval
                tt = sec['time']
                dur = tt[1] - tt[0]
                xgrid_locs += tt  # add the boundaries to grid locations

                # get the plot limits
                ylim = ax3.get_ylim()

                # get the color code for the section
                clr = colors[unique_sections.index(sec['name'])]

                # create the rectangle
                p = patches.Rectangle((tt[0], ylim[0]), dur, ylim[1],
                                      alpha=0.3, facecolor=clr,
                                      edgecolor='black')
                ax4.add_patch(p)

                sec_labels.append(sec['name'])
                sec_locs.append(np.mean(tt))

            # styling
            ax4.set_xticks(sec_locs)
            ax4.set_xticklabels(sec_labels, rotation=-15)

            ax1.set_xticks(xgrid_locs, minor=True)
            ax1.xaxis.grid(True, which='minor')
            ax1.xaxis.set_major_locator(FixedLocator(
                xgrid_locs, nbins=len(xgrid_locs) / 2 + 1))

            plt.setp(ax4.get_yticklabels(), visible=False)
            ax4.set_xlim(ax3.get_xlim())
        else:
            # no section labels
            plt.setp(ax4.get_xticklabels(), visible=False)

    @staticmethod
    def _plot_performed_notes(ax, notes):
        for note in notes:
            ax.plot(note['interval'], [note['performed_pitch']['value'],
                                       note['performed_pitch']['value']],
                    'r', alpha=0.4, linewidth=4)

    @classmethod
    def _plot_note_models(cls, ax2, note_models, pitch_distribution):
        max_rel_occur = cls._get_relative_note_occurences(
            note_models, pitch_distribution)

        cls._plot_note_distributions(ax2, note_models)

        ytick_vals = cls._plot_stable_pitches(
            ax2, max_rel_occur, note_models, max(pitch_distribution.vals))

        return ytick_vals

    @staticmethod
    def _plot_stable_pitches(ax, max_rel_occur, note_models, max_pd_height):
        ytick_vals = []
        for note_symbol, note in iteritems(note_models):
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
        for note_symbol, note in iteritems(note_models):
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
        for note_symbol, note in iteritems(note_models):
            try:
                ax.plot(note_models[note_symbol]['distribution'].vals,
                        note_models[note_symbol]['distribution'].bins,
                        label=note_symbol)
            except KeyError:
                logging.debug(u'note model is not available for {0:s}'.format(
                    note_symbol))

    @staticmethod
    def _plot_annotations(ax, makam, tonic, transposition, tempo):
        anno_str = []

        # makam
        if makam is not None:
            anno_str.append(u'{0:s} makam'.format(makam))

        # don't append it yet, it will be after tonic
        if transposition is not None:
            tonic_symbol = transposition['tonic_symbol']
            anno_str.append(u'{0:s} ahenk'.format(transposition['name']))
        else:
            tonic_symbol = '?'

        if tonic is not None:
            # insert before transposition
            anno_str.insert(1, u'{0:s} = {1:.1f} Hz'.
                            format(tonic_symbol, tonic['value']))

        if tempo is not None:
            anno_str.append(u'Av. Tempo: {0:d} bpm'.
                            format(int(tempo['average']['value'])))
            
            rel_tempo_percentage = int(100*(tempo['relative']['value'] - 1))
            anno_str.append(u'Performed {0:d}% faster'.
                            format(rel_tempo_percentage))

        anno_str = u'\n'.join(anno_str)

        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.annotate(anno_str, xy=(0, 0), ha="center", va="center")
        ax.axis('off')
