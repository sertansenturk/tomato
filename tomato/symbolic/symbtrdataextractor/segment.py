from . scoreprocessor import ScoreProcessor
from . structurelabeler import StructureLabeler


class SegmentExtractor(object):
    """

    """
    def __init__(self, lyrics_sim_thres=0.70, melody_sim_thres=0.70,
                 save_structure_sim=True, crop_consecutive_bounds=True):
        """
        Class constructor

        Parameters
        ----------
        lyrics_sim_thres : float[0, 1], optional
            The similarity threshold for the lyrics of two segments
            to be regarded as similar. (the default is 0.75)
        melody_sim_thres : float[0, 1], optional
            The similarity threshold for the melody of two segments
            to be regarded as similar. (the default is 0.75)
        save_structure_sim : bool, optional
            True to add the melodic and lyrics similarity between each
            section and segment to the output, False otherwise
        crop_consecutive_bounds : bool, optional
            True to remove the first of the two consecutive boundaries,
            False otherwise. (the default is True)
        """
        self.lyrics_sim_thres = lyrics_sim_thres
        self.melody_sim_thres = melody_sim_thres
        self.save_structure_sim = save_structure_sim
        self.crop_consecutive_bounds = crop_consecutive_bounds

        self.segmentLabeler = StructureLabeler(
            save_structure_sim=self.save_structure_sim,
            lyrics_sim_thres=self.lyrics_sim_thres,
            melody_sim_thres=self.melody_sim_thres)

    def extract_phrases(self, score, sections=None):
        # code 51 is the usul change and it always marks a segment boundary
        bound_codes = [51, 53, 54, 55]
        anno_codes = [53, 54, 55]

        # get all boundaries starting with the first note
        all_bounds = self._get_all_bounds_in_score(bound_codes, score)

        # if there are only usul boundaries the score does not have annotations
        anno_bounds = [i for i, code in enumerate(score['code'])
                       if code in anno_codes]

        if anno_bounds:
            phrases = self._extract(all_bounds, score, sections=sections,
                                    segment_str='PHRASE')
        else:
            phrases = []

        return phrases

    def extract_segments(self, score, segment_note_bound_idx, sections=None):
        try:
            if segment_note_bound_idx:
                # convert from Symbtr index (starting from 1) to python index
                bounds = [b - 1 for b in segment_note_bound_idx]

                segments = self._extract(bounds, score, sections=sections,
                                         segment_str='SEGMENT')
            else:
                segments = []
        except TypeError:  # the json saved by automatic phrase segmentation
            # (https://github.com/MTG/makam-symbolic-phrase-segmentation)
            # has a special structure specifying the 0 dimensional array
            segments = []

        return segments

    def _extract(self, bounds, score, sections=None, segment_str='SEGMENT'):
        # add the first and the last bound if they are not already given,
        # sort & tidy
        bounds = self._parse_bounds(bounds, score)
        segments = []
        for pp in range(0, len(bounds) - 1):
            start_note_idx = bounds[pp]
            end_note_idx = bounds[pp + 1] - 1

            # cesni/flavor
            flavor = self._get_segment_flavor_idx(score, start_note_idx,
                                                  end_note_idx)

            # lyrics
            lyrics = ScoreProcessor.get_lyrics_between(score, start_note_idx,
                                                       end_note_idx)

            # sections the segment is in
            segment_sections = []
            if sections:
                start_section_idx = self._get_section_idx(sections,
                                                          start_note_idx)
                end_section_idx = self._get_section_idx(sections, end_note_idx)

                for idx, sec in zip(range(start_section_idx,
                                          end_section_idx + 1),
                                    sections[start_section_idx:
                                             end_section_idx + 1]):
                    segment_sections.append(
                        {'section_idx': idx,
                         'melodic_structure': sec['melodic_structure'],
                         'lyrics_structure': sec['lyrics_structure']})

            name, slug = self._name_segment(lyrics, segment_str)

            # append section
            segments.append({'name': name, 'slug': slug, 'flavor': flavor,
                             'lyrics': lyrics, 'sections': segment_sections,
                             'start_note': start_note_idx,
                             'end_note': end_note_idx})

        segments = self.segmentLabeler.label_structures(segments, score)

        # map the python indices in start_note and end_note to SymbTr index
        self.segmentLabeler.python_idx_to_symbtr_idx(segments, score)

        return segments

    @staticmethod
    def _name_segment(lyrics, segment_str):
        if lyrics:
            name = u"VOCAL_" + segment_str
            slug = u"VOCAL_" + segment_str
        else:
            name = u"INSTRUMENTAL_" + segment_str
            slug = u"INSTRUMENTAL_" + segment_str

        return name, slug

    @staticmethod
    def _get_all_bounds_in_score(bound_codes, score):
        # start bounds with the first note
        first_note_idx = ScoreProcessor.get_first_note_index(score)

        all_bounds = [first_note_idx]
        for i, code in enumerate(score['code']):
            if code in bound_codes and i > first_note_idx:
                all_bounds.append(i)

        return all_bounds

    @staticmethod
    def _get_segment_flavor_idx(score, start_note_idx, end_note_idx):
        flavor = []
        for i, code in enumerate(
                score['code'][start_note_idx:end_note_idx + 1]):
            if code == 54:
                flavor.append(score['lyrics'][start_note_idx + i])

        return flavor

    @staticmethod
    def _get_section_idx(sections, note_idx):
        # there should be only one but we accumulate the resulting index in
        # an array for the asserting later
        section_idx = []
        for i, sec in enumerate(sections):
            # the section indices are given as symbtr indexing (from 1)
            # convert them to python indexing
            sec_start_idx = sec['start_note'] - 1
            sec_end_idx = sec['end_note'] - 1
            if sec_start_idx <= note_idx <= sec_end_idx:
                section_idx.append(i)

        assert len(section_idx) == 1, 'Unexpected indexing: the note should ' \
                                      'have been in a single section'

        return section_idx[0]

    def _parse_bounds(self, bounds, score):
        # add start and end if they are not already in the list
        first_bound_idx = ScoreProcessor.get_first_note_index(score)
        bounds.insert(0, first_bound_idx)

        # create the boundary outside the score idx
        last_bound_idx = len(score['code'])
        bounds += [last_bound_idx]

        bounds = sorted(list(set(bounds)))  # sort and tidy

        # remove consecutive boundaries
        if self.crop_consecutive_bounds:
            self._crop_consec_bounds(bounds, first_bound_idx)

        # check boundaries
        all_bounds_in_score = all(last_bound_idx >= b >= first_bound_idx
                                  for b in bounds)
        assert all_bounds_in_score, 'one of the bounds is outside the score.'

        return bounds

    @staticmethod
    def _crop_consec_bounds(bounds, first_bound_idx):
        # find the boundary indices to pop. Don't pop them immediately,
        # as there can be more than two consecutive boundaries and
        # premature pop will leave some untouched
        del_idx = []
        next_to_start_idx = [first_bound_idx + 1]
        for i in range(0, len(bounds) - 1):
            if bounds[i + 1] - bounds[i] == 1:
                if bounds[i + 1] - 1 in next_to_start_idx:
                    # if there are consecutive bounds in the start,
                    # pop all except the first bound
                    del_idx.append(i + 1)
                    next_to_start_idx.append(i + 1)
                else:
                    # if there are two consecutive bounds, pop the first
                    del_idx.append(i)

        for index in sorted(del_idx, reverse=True):
            del bounds[index]
