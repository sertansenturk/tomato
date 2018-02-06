from .metadata.metadataextractor import MetadataExtractor
import warnings


class RhythmicFeatureExtractor(object):
    """

    """
    @classmethod
    def extract_rhythmic_structure(cls, score):
        usul_bounds = [ii for ii, code in enumerate(score['code'])
                       if code == 51]
        usul_dict = MetadataExtractor.get_attribute_dict('usul')

        rhythmic_structure = []
        for ii, ub in enumerate(usul_bounds):
            start = score['index'][ub]
            if ii < len(usul_bounds) - 1:
                end = score['index'][usul_bounds[ii + 1] - 1]
            else:  # end of file
                end = score['index'][len(score['code']) - 1]

            usul_key = RhythmicFeatureExtractor.get_usul_symbtr_slug(
                score, ub, usul_dict)

            usul = {'attribute_key': usul_key, 'mu2_name': score['lyrics'][ub],
                    'mertebe': score['denumerator'][ub],
                    'number_of_pulses': score['numerator'][ub],
                    'symbtr_internal_id': score['lns'][ub]}

            # compute the tempo from the next note
            tempo = cls.compute_tempo_from_next_note(score, ub, usul)

            rhythmic_structure.append(
                {'usul': usul, 'tempo': {'value': tempo, 'unit': 'bpm'},
                 'startNote': start, 'endNote': end})

        return rhythmic_structure

    @staticmethod
    def get_usul_symbtr_slug(score, usul_bound, usul_dict):
        # search the usul slug
        for usul_key, usul in usul_dict.iteritems():
            for var in usul['variants']:
                if score['lyrics'][usul_bound] == var['mu2_name']:
                    return usul_key

        # Keep it as a warning, not assertion, so we can also process faulty
        # scores
        warnstr = u'{0:s} in location {1:d} is missing in usul_dict'.format(
            score['lyrics'][usul_bound], usul_bound + 1)
        warnings.warn(warnstr.encode('utf-8'), stacklevel=2)
        return None

    @classmethod
    def compute_tempo_from_next_note(cls, score, usul_boundary, usul):
        tempo = None
        if usul['mu2_name'] == '[Serbest]':
            pass  # no tempo for non-metered score
        else:
            it = usul_boundary
            while not tempo:
                it += 1
                if score['code'][it] == 9:  # proper note
                    tempo = cls._compute_tempo_from_note(
                        score['numerator'][it], score['denumerator'][it],
                        score['duration'][it], usul['mertebe'])
        return tempo

    @staticmethod
    def _compute_tempo_from_note(note_num, note_denum, note_dur, mertebe):
        sym_dur = float(note_num) / note_denum
        rel_dur_wrt_mertebe = mertebe * sym_dur * 0.001

        tempo = int(round(60.0 / (note_dur * rel_dur_wrt_mertebe)))

        return tempo
