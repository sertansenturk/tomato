import os

from .metadata.metadataextractor import MetadataExtractor
from .reader.txt import TxtReader
from .reader.musicxml import MusicXMLReader
from .reader.mu2 import Mu2Reader
from .rhythmicfeature import RhythmicFeatureExtractor
from .section import SectionExtractor
from .segment import SegmentExtractor
from .datamerger import DataMerger


class DataExtractor(DataMerger):
    """
    The class to extract the relevant information from a SymbTr score.

    The information include:
        * Obtain the makam, usul, form, name and composer of the given SymbTr
        score
        * Extract section boundaries from both the implicit and explicit
        section information given in the SymbTr scores
        * Extract annotated phrase boundaries in the SymbTr scores
        * Add user provided segment boundaries in the SymbTr scores
        * Analyse the melody and the lyrics of the sections, phrase
        annotations and user provided segmentations, and apply semiotic labels
        * Query relevant metadata from MusicBrainz (if the MBID is supplied)

    Currently only the SymbTr-txt scores are supported. MusicXML and mu2
    support can be added, if demanded.
    """

    def __init__(self, lyrics_sim_thres=0.7, melody_sim_thres=0.7,
                 save_structure_sim=True, extract_all_labels=False,
                 crop_consec_bounds=True, get_recording_rels=False,
                 print_warnings=True):
        """
        Class constructor

        Parameters
        ----------
        lyrics_sim_thres : float[0, 1], optional
            The similarity threshold for the lyrics of two sections/segments
            to be regarded as similar. (the default is 0.75)
        melody_sim_thres : float[0, 1], optional
            The similarity threshold for the melody of two sections/segments
            to be regarded as similar. (the default is 0.75)
        save_structure_sim : bool, optional
            True to add the melodic and lyrics similarity between each
            section and segment to the output, False otherwise
        extract_all_labels : bool, optional
            True to extract sections using all labels in written in the lyrics
            field regardless they are a section marking etc., False to only
            extract the lyrics. (the default is False)
        crop_consec_bounds : bool, optional
            True to remove the first of the two consecutive boundaries inside
            user given segmentation boundaries, False otherwise. (the
            default is True)
        get_recording_rels : bool, optional
            True to query the recording relations related to the score from
            MusicBrainz False otherwise. When calling the extract method the
            relevant (work) MBID should be supplied. If the supplied MBID
            belongs to a recording, this flag will not provide to extra
            information, since the recording metadata will be crawled anyways.
            (the default is False)
        print_warnings : bool, optional
            True to display warnings, False otherwise. Note that the errors
            and the inconsistencies in the scores will be always displayed
            (the default is True)
        """
        self._metadata_extractor = MetadataExtractor(
            get_recording_rels=get_recording_rels)

        self._section_extractor = SectionExtractor(
            lyrics_sim_thres=lyrics_sim_thres,
            melody_sim_thres=melody_sim_thres,
            save_structure_sim=save_structure_sim,
            extract_all_labels=extract_all_labels,
            print_warnings=print_warnings)

        self._segment_extractor = SegmentExtractor(
            lyrics_sim_thres=lyrics_sim_thres,
            melody_sim_thres=melody_sim_thres,
            save_structure_sim=save_structure_sim,
            crop_consecutive_bounds=crop_consec_bounds)

    def extract(self, score_file, symbtr_name=None, mbid=None,
                segment_note_bound_idx=None):
        """
        Extracts the relevant (meta)data from the SymbTr score.

        Parameters
        ----------
        score_file : str
            The path of the SymbTr score
        symbtr_name : str, optional
            The name of the score in SymbTr naming convention
            (makam--form--usul--name--composer). Needed if the filename does
            not obey this convention. If not provided the method will
            attempt to recover the symbtr_name from the score_file input.
            (the default is None, which implies the name will be recovered
            from symbtr_file)
        mbid : str, optional
            The `MBID <https://musicbrainz.org/doc/MusicBrainz_Identifier>`_
            relevant to the SymbTr score. For the score of a composition the
            work mbid of the composition should be supplied. For the score
            of a transcribed recording the identifier should be a recording
            MBID. The MBID can either be given as the 36 character uuid
            (83291c8a-4ef1-4ffc-8b50-3fc03890f5a4) or as an html link
            (https://musicbrainz.org/work/83291c8a-4ef1-4ffc-8b50
            -3fc03890f5a4). In the first case the method will try to find
            whether the MBID belongs to a work or a recording automatically.
            (the default is None)
        segment_note_bound_idx : list[ind], optional
            Boundary indices obtained from user provided (automatic)
            segmentation.
            Currently this parameter is only supported for the SymbTr-txt
            scores. For automatic segmentation from the SymbTr-txt
            scores, you can use the `makam-symbolic-phrase-segmentation
            <https://github.com/MTG/makam-symbolic-phrase-segmentation>`_
            package. (the default is None)

        Returns
        ----------
        dict
            A dictionary storing all the relevant (meta)data
        bool
            True if the information bout the score is all valid/consistent,
            False otherwise

        Raises
        ------
        ValueError
            If either of melody_sim_thres or lyrics_sim_thres imputs is
            outside [0,1]
        """
        if symbtr_name is None:
            symbtr_name = os.path.splitext(os.path.basename(score_file))[0]

        # get the metadata
        data, is_metadata_valid = self._metadata_extractor.get_metadata(
            symbtr_name, mbid=mbid)

        # get the extension to determine the SymbTr-score format
        extension = os.path.splitext(score_file)[1]

        # read the score
        score, is_score_content_valid = self._read_score(
            extension, score_file, symbtr_name)

        data['duration'] = {'value': sum(score['duration']) * 0.001,
                            'unit': 'second'}
        data['number_of_notes'] = len(score['duration'])

        data['sections'], is_section_data_valid = self._section_extractor. \
            from_txt_score(score, symbtr_name)

        anno_phrases = self._segment_extractor.extract_phrases(
            score, sections=data['sections'])
        segments = self._segment_extractor.extract_segments(
            score, segment_note_bound_idx, sections=data['sections'])

        data['rhythmic_structure'] = \
            RhythmicFeatureExtractor.extract_rhythmic_structure(score)

        data['segments'] = segments
        data['phrase_annotations'] = anno_phrases

        is_data_valid = all([is_metadata_valid, is_section_data_valid,
                             is_score_content_valid])

        return data, is_data_valid

    @staticmethod
    def _read_score(extension, score_file, symbtr_name):
        if extension == ".txt":
            score, is_score_content_valid = TxtReader.read(
                score_file, symbtr_name=symbtr_name)
        elif extension == ".xml":
            score, is_score_content_valid = MusicXMLReader.read(
                score_file, symbtr_name=symbtr_name)
        elif extension == ".mu2":
            score, is_score_content_valid = Mu2Reader.read(
                score_file, symbtr_name=symbtr_name)
        else:
            raise IOError("Unknown format")
        return score, is_score_content_valid

    # getter and setters
    @property
    def lyrics_sim_thres(self):
        self._assert_sim_threshold('lyrics')
        return self._segment_extractor.lyrics_sim_thres

    @lyrics_sim_thres.setter
    def lyrics_sim_thres(self, value):
        self._set_sim_thres(value, 'lyrics')

    @property
    def melody_sim_thres(self):
        self._assert_sim_threshold('melody')

        return self._segment_extractor.melody_sim_thres

    @melody_sim_thres.setter
    def melody_sim_thres(self, value):
        self._set_sim_thres(value, 'melody')

    def _assert_sim_threshold(self, name):
        p = name + '_sim_thres'
        segment_sim_thres = getattr(self._segment_extractor, p)
        section_sim_thres = getattr(self._section_extractor, p)
        assert segment_sim_thres == section_sim_thres, \
            u'The {0:s} of the _segmentExtractor and _sectionExtractor ' \
            u'should have the same value'.format(p)

    def _set_sim_thres(self, value, name):
        self._chk_sim_thres_val(value)
        setattr(self._segment_extractor, name + '_sim_thres', value)
        setattr(self._section_extractor, name + '_sim_thres', value)

    @staticmethod
    def _chk_sim_thres_val(value):
        if not 0 <= value <= 1:
            raise ValueError('The similarity threshold should be a float '
                             'between [0, 1]')

    @property
    def extract_all_labels(self):
        return self._section_extractor.extract_all_labels

    @extract_all_labels.setter
    def extract_all_labels(self, value):
        self._chk_bool(value)
        self._section_extractor.extract_all_labels = value

    @property
    def print_warnings(self):
        return self._section_extractor.print_warnings

    @print_warnings.setter
    def print_warnings(self, value):
        self._chk_bool(value)
        self._section_extractor.print_warnings = value

    @property
    def get_recording_rels(self):
        return self._metadata_extractor.get_recording_rels

    @get_recording_rels.setter
    def get_recording_rels(self, value):
        self._chk_bool(value)
        self._metadata_extractor.get_recording_rels = value

    @property
    def crop_consecutive_bounds(self):
        return self._segment_extractor.crop_consecutive_bounds

    @crop_consecutive_bounds.setter
    def crop_consecutive_bounds(self, value):
        self._chk_bool(value)
        self._segment_extractor.crop_consecutive_bounds = value

    @staticmethod
    def _chk_bool(value):
        if not isinstance(value, type(True)):
            raise ValueError('The property should be a boolean')
