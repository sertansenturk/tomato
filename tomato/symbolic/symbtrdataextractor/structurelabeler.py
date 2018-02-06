from .scoreprocessor import ScoreProcessor
from .graph import GraphOperations
from copy import deepcopy


class StructureLabeler(object):
    """

    """

    def __init__(self, lyrics_sim_thres=0.7, melody_sim_thres=0.7,
                 save_structure_sim=True):
        self.lyrics_sim_thres = lyrics_sim_thres
        self.melody_sim_thres = melody_sim_thres
        self.save_structure_sim = save_structure_sim

    def label_structures(self, structures, score):
        # get the duration, pitch and lyrics related to the section
        score_fragments = []
        for s in structures:
            durs = self._get_score_key_in_structure(s, score, 'duration')
            nums = self._get_score_key_in_structure(s, score, 'numerator')
            denums = self._get_score_key_in_structure(s, score, 'denumerator')
            notes = self._get_score_key_in_structure(s, score, 'comma53')
            lyrics = self._get_score_key_in_structure(s, score, 'lyrics')

            score_fragments.append({'durs': durs, 'nums': nums,
                                    'denums': denums, 'notes': notes,
                                    'lyrics': lyrics})

        if structures:
            # get the lyric organization
            self.get_lyrics_organization(structures, score_fragments)

            # get the melodic organization
            self.get_melodic_organization(structures, score_fragments)

        return structures

    @staticmethod
    def python_idx_to_symbtr_idx(structures, score):
        for st in structures:
            st['start_note'] = score['index'][st['start_note']]
            st['end_note'] = score['index'][st['end_note']]

    @staticmethod
    def _get_score_key_in_structure(s, score, name):
        return score[name][s['start_note']:s['end_note'] + 1]

    def get_lyrics_organization(self, structures, score_fragments):
        # Here we only check whether the lyrics are similar to others
        # We don't check whether they are sung on the same note / with
        # the same duration, or not. As a results, two structures having
        # exactly the same melody but different sylallable onset/offsets
        # would be considered the same. Nevertheless this situation
        # would occur in very rare occasions.
        # From the point of view of an audio-score alignment algorithm
        # using only melody, this function does not give any extra info
        # This part is done for future needs; e.g. audio-lyrics alignment

        # get the lyrics stripped of section information
        lyrics = ScoreProcessor.get_true_lyrics(score_fragments)
        for (sf, ly) in zip(score_fragments, lyrics):
            sf['lyrics'] = ly  # assign lyrics to the relevant score_fragments

        # graph analysis
        lyrics_strings = [a['lyrics'] for a in score_fragments]
        dists = GraphOperations.get_dist_matrix(lyrics_strings,
                                                metric='norm_levenshtein')
        cliques = GraphOperations.get_cliques(dists, self.lyrics_sim_thres)

        # semiotic labeling
        lyrics_labels = self._semiotize(cliques)
        self._apply_labels_to_lyrics_structure(
            structures, lyrics_labels, score_fragments, dists)

        # sanity check
        self._assert_labels(lyrics, lyrics_labels, 'lyrics')

    def get_melodic_organization(self, structures, score_fragments):
        melodies, melody_strings = self.get_melodies(score_fragments)

        dists = GraphOperations.get_dist_matrix(melody_strings,
                                                metric='norm_levenshtein')
        cliques = GraphOperations.get_cliques(dists, self.melody_sim_thres)

        melody_labels = self._semiotize(cliques)

        # label the structures
        for i in range(0, len(melody_labels)):
            structures[i]['melodic_structure'] = melody_labels[i]
            if self.save_structure_sim:
                structures[i]['melodic_similarities'] = \
                    (1 - dists[i, :]).tolist()[0]

        # sanity check
        self._assert_labels(melodies, melody_labels, 'melody')

    def get_melodies(self, score_fragments):
        score_fragments_copy = self._remove_zero_dur_events(score_fragments)

        # synthesize the score by taking the shortest note as the unit
        # (i.e. the shortest note has the largest denumerator)
        max_denum = max(max(sf['denums']) for sf in score_fragments_copy)
        melodies = [ScoreProcessor.synth_melody(sf, max_denum)
                    for sf in score_fragments_copy]

        # convert the numbers in melodies to unique strings for Levenstein dist
        melody_strings = self._melodies_to_strings(
            melodies, score_fragments_copy)

        return melodies, melody_strings

    @staticmethod
    def _melodies_to_strings(melodies, score_fragments_copy):
        unique_notes = list(set(x for sf in score_fragments_copy
                                for x in sf['notes']))
        melody_strings = [ScoreProcessor.mel2str(m, unique_notes)
                          for m in melodies]
        return melody_strings

    @staticmethod
    def _remove_zero_dur_events(score_fragments):
        copy_fragments = deepcopy(score_fragments)

        # remove annotation/control row; i.e. entries w 0 duration
        for sf in copy_fragments:
            for i in reversed(range(0, len(sf['durs']))):
                if sf['durs'][i] == 0:
                    sf['notes'].pop(i)
                    sf['nums'].pop(i)
                    sf['denums'].pop(i)
                    sf['durs'].pop(i)

        return copy_fragments

    def _apply_labels_to_lyrics_structure(
            self, structures, lyrics_labels, score_fragments, dists):

        for i in range(0, len(lyrics_labels)):
            # if there's no lyrics, label instrumental
            if not score_fragments[i]['lyrics']:
                structures[i]['lyrics_structure'] = 'INSTRUMENTAL'
            else:
                structures[i]['lyrics_structure'] = lyrics_labels[i]

            if self.save_structure_sim:
                structures[i]['lyrics_similarities'] = \
                    (1 - dists[i, :]).tolist()[0]

    @staticmethod
    def _assert_labels(stream, labels, name):
        for lbl, strm in zip(labels, stream):
            chk_strm = ([stream[i] for i, x in enumerate(labels)
                         if x == lbl])
            assert all(strm == cl for cl in chk_strm), \
                'Mismatch in {0!s} label: {1!s}'.format(name, lbl)

    @classmethod
    def _semiotize(cls, cliques):
        # Here we follow the annotation conventions explained in:
        #
        # Frederic Bimbot, Emmanuel Deruty, Gabriel Sargent, Emmanuel Vincent.
        # Semiotic structure labeling of music pieces: Concepts, methods and
        # annotation conventions. 13th International Society for Music
        # Information Retrieval Conference (ISMIR), Oct 2012, Porto, Portugal.
        # 2012. <hal-00758648>
        # https://hal.inria.fr/file/index/docid/758648/filename/bimbot_ISMIR12.pdf
        #
        # Currently we only use the simplest labels, e.g. A, A1, B and AB
        num_nodes = len(set.union(*cliques['exact']))
        labels = ['?'] * num_nodes  # labels to fill for each note

        # define clique indices for labeling the exact cliques
        sim_clq_it = [1] * len(cliques['similar'])  # similar cliques indices
        mix_clq_it = dict()  # initialize the mixture clique indices

        # similar cliques give us the base structure
        basenames = cls._get_basenames(cliques['similar'])
        for ec in cliques['exact']:
            # find the similar cliques of which the current exact clique is
            # a subset of
            sim_clique_idx = cls._get_similar_clique_idx(
                cliques, ec)

            if len(sim_clique_idx) == 1:  # belongs to one similar clique
                for e in sorted(ec):  # label with basename + number
                    labels[e] = (basenames[sim_clique_idx[0]] +
                                 str(sim_clq_it[sim_clique_idx[0]]))
                sim_clq_it[sim_clique_idx[0]] += 1
            else:  # belongs to more than one similar clique
                cls._label_mixture_clique(
                    ec, labels, sim_clique_idx, mix_clq_it, basenames)

        return labels

    @staticmethod
    def _label_mixture_clique(ec, labels, sim_clique_idx, mix_clq_it,
                              basenames):
        mix_str = ''.join([basenames[i] for i in sim_clique_idx])
        if mix_str not in mix_clq_it.keys():
            mix_clq_it[mix_str] = 1
        for e in ec:  # join the labels of all basenames
            labels[e] = mix_str + str(mix_clq_it[mix_str])
        mix_clq_it[mix_str] += 1

    @staticmethod
    def _get_basenames(similar_cliques):
        # define the upper case unicode letters for semiotic labeling
        unicode_letters = [unichr(i) for i in range(0, 1000)
                           if unicode.isupper(unichr(i))]

        # similar cliques give us the base structure
        basenames = [unicode_letters[i]
                     for i in range(0, len(similar_cliques))]

        return basenames

    @staticmethod
    def _get_similar_clique_idx(cliques, ec):
        in_cliques_idx = [i for i, x in enumerate(cliques['similar'])
                          if ec <= x]
        assert len(in_cliques_idx) > 0,\
            "The exact clique is not in the similar cliques list. " \
            "This shouldn't happen."

        return in_cliques_idx
