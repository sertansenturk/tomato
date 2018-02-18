# coding=utf-8
from __future__ import unicode_literals, division
import warnings
import xml.etree.ElementTree as eT
from xml.etree.ElementTree import ParseError

__author__ = 'hsercanatli', 'burakuyar', 'andresferrero', 'sertansenturk'


class MusicXMLReader(object):
    makam_accidentals = {'quarter-flat': '-1',
                         'slash-flat': '-4',
                         'flat': '-5',
                         'double-slash-flat': '-8',
                         'quarter-sharp': '+1',
                         'sharp': '+4',
                         'slash-quarter-sharp': '+5',
                         'slash-sharp': '+8'}

    @classmethod
    def read(cls, xml_in):
        """
        :param xml_in:
        :rtype: object
        """

        # setting the xml tree
        parser = _XMLCommentHandler()
        try:
            try:  # document
                tree = eT.parse(xml_in, parser)
                root = tree.getroot()
            except IOError:  # string input
                root = eT.fromstring(xml_in, parser)
        except ParseError:
            raise ParseError("Line 36(ish): Error parsing MusicXML file.")

        # getting key signatures
        keysig = cls._get_key_signature(root)

        # makam, form and usul information
        makam, form, usul = cls._get_makam_form_usul(root)

        # work title
        work_title = cls._get_title(root)

        # composer and lyricist
        composer, lyricist = cls._get_composer_lyricist(root)

        # reading the xml measure by measure
        measures, time_sigs = cls._get_measures(root)

        return (measures, makam, usul, form, time_sigs, keysig,
                work_title, composer, lyricist)

    @staticmethod
    def _get_key_signature(root):
        keysig = {}  # keys: notes, values: type of note accident
        for xx, key in enumerate(
                root.findall('part/measure/attributes/key/key-step')):
            keysig[key.text] = root.findall(
                'part/measure/attributes/key/key-accidental')[xx].text

        return keysig

    @staticmethod
    def _get_makam_form_usul(root):
        if root.find('part/measure/direction/direction-type/words').text:
            # the information is stored in the form below:
            # "Makam: [makam], Form: [form], Usul: [usul] "
            cultural_info = root.find(
                'part/measure/direction/direction-type/words').text

            attributes = []
            for info in cultural_info.split(","):
                attributes.append(''.join(info.split(": ")[1]).strip())

            makam, form, usul = attributes
        else:
            warnings.warn("Makam, Form and Usul information do not exist.")
            makam = form = usul = ''

        return makam, form, usul

    @staticmethod
    def _get_title(root):
        if root.find('work/work-title').text:
            work_title = ''.join(root.find('work/work-title').text).strip()
        else:
            work_title = ''.strip()

        return work_title

    @staticmethod
    def _get_composer_lyricist(root):
        identification = [item.text for item in root.findall(
            'identification/creator')]
        if len(identification) == 2:
            composer = ''.join(identification[0]).strip()
            lyricist = ''.join(identification[1]).strip()
        else:
            composer = ''.join(identification[0]).strip()
            lyricist = ''.strip()
        return composer, lyricist

    @classmethod
    def _get_measures(cls, root):
        # tempo
        bpm = float(root.find('part/measure/direction/sound').attrib['tempo'])
        divisions = float(root.find('part/measure/attributes/divisions').text)
        quarter_note_len = 60000.0 / bpm

        beat_type = root.find('part/measure/attributes/time/beat-type').text
        beats = root.find('part/measure/attributes/time/beats').text

        # read measures
        measures = []
        time_sigs = {}
        for measure_index, measure in enumerate(root.findall('part/measure')):
            # check time signature changes
            time_sig_change = measure.find('attributes/time')
            if time_sig_change is not None:
                beat_type = time_sig_change.find('beat-type').text
                beats = time_sig_change.find('beats').text
                time_sigs[measure_index] = {'beat_type': beat_type,
                                            'beats': beats}

            # read notes/rests
            temp_measure = []
            # all notes in the current measure
            for note_index, note in enumerate(measure.findall('note')):
                # symbtr-txt id, which is stored in MusicXML
                symbtr_txt_id = cls._get_symbtr_txt_id(note)

                # rest
                rest = cls._chk_rest(note)

                # pitch and octave information of the current note
                pitch_step, octave = cls._get_pitchstep_octave(note, rest)

                # symbolic duration without considering dotted, tuple etc. The
                # duration info will be handled properly during the LilyPond
                # conversion
                normal_dur = cls._get_normal_dur(note, divisions,
                                                 quarter_note_len)

                # accident inf
                acc = cls._get_accidental(note)

                # dotted or not
                dot = cls._chk_dotted(note)

                # tuplet or not
                tuplet = cls._chk_tuplet(note)

                # lyrics
                lyrics = cls._get_lyrics(note)

                # appending attributes to the temp note
                temp_note = [pitch_step, octave, acc, dot, tuplet, rest,
                             normal_dur, symbtr_txt_id, lyrics]

                temp_measure.append(temp_note)

            # add temp measure to the measure
            measures.append(temp_measure)

        assert 0 in time_sigs.keys(), \
            'The MusicXML score does not start with a time signature'
        return measures, time_sigs

    @staticmethod
    def _get_pitchstep_octave(note, rest):
        if rest:
            pitch_step = 'r'
            octave = 'r'
        elif note.find('pitch') is not None:  # pitch
            pitch_step = note.find('pitch/step').text.lower()
            octave = note.find('pitch/octave').text
        else:
            raise ValueError("The element should have been a note or "
                             "rest")

        return pitch_step, octave

    @staticmethod
    def _get_symbtr_txt_id(note):
        if note.find("symbtrid").text:
            return int(note.find("symbtrid").text)
        else:
            return None

    @staticmethod
    def _chk_rest(note):
        return note.find('rest') is not None

    @staticmethod
    def _get_normal_dur(note, divisions, quarter_note_len):
        if note.find('duration') is None:  # grace note
            return None
        else:
            dur = note.find('duration').text  # get the true duration
            return (int(quarter_note_len * float(dur) / divisions) /
                    quarter_note_len)

    @classmethod
    def _get_accidental(cls, note):
        if note.find('accidental') is not None:
            return cls.makam_accidentals[note.find('accidental').text]
        else:
            return 0

    @staticmethod
    def _chk_dotted(note):
        return note.find('dot') is not None

    @staticmethod
    def _chk_tuplet(note):
        return note.find('time-modification') is not None

    @staticmethod
    def _get_lyrics(note):
        if note.find('lyric/text').text is not None:
            return note.find('lyric/text').text
        else:
            return ''


class _XMLCommentHandler(eT.XMLTreeBuilder):
    def __init__(self):
        super(_XMLCommentHandler, self).__init__()

        # assumes ElementTree 1.2.X
        self._parser.CommentHandler = self.handle_comment

    def handle_comment(self, data):
        self._target.start("symbtrid", {})
        if data and 'symbtr_txt_note_index' in data:
            data = data.replace('symbtr_txt_note_index ', '')
        self._target.data(data)
        self._target.end("symbtrid")
