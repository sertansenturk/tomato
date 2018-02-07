# coding=utf-8
from __future__ import unicode_literals, division
from musicxmlreader import MusicXMLReader
import os
import sqlite3

__author__ = 'hsercanatli', 'burakuyar', 'andresferrero', 'sertansenturk'


class ScoreConverter(object):
    _octaves = {"2": ",", "3": "", "4": "\'", "5": "\'\'", "6": "\'\'\'",
                "7": "\'\'\'\'", "r": ""}

    _accidentals = {"-1": "fc", "-4": "fb", "-5": "fk", "-8": "fbm",
                    "1": "c", "4": "b", "5": "k", "8": "bm", "0": ""}

    # notes and accidentals dictionary lilypond
    _notes_western2lily = {"g": "4", "a": "5", "b": "6", "c": "0",
                           "d": "1", "e": "2", "f": "3"}

    _key_sig_accidentals = {'double-slash-flat': "(- BUYUKMUCENNEP)",
                            'flat': "(- KUCUK)",
                            'slash-flat': "(- BAKIYE)",
                            'quarter-flat': "(- KOMA)",
                            'slash-sharp': "BUYUKMUCENNEP",
                            'slash-quarter-sharp': "KUCUK",
                            'sharp': "BAKIYE",
                            'quarter-sharp': "KOMA"}

    _makam_accidentals = {'quarter-flat': '-1',
                          'slash-flat': '-4',
                          'flat': '-5',
                          'double-slash-flat': '-8',
                          'quarter-sharp': '+1',
                          'sharp': '+4',
                          'slash-quarter-sharp': '+5',
                          'slash-sharp': '+8'}

    # sorting rules of key signatures
    sort_rule_sharps = {'F': 0, 'C': 1, 'G': 2, 'D': 3, 'A': 4, 'E': 5,
                        'B': 6}
    sort_rule_notes_sharps = {0: 'F', 1: 'C', 2: 'G', 3: 'D', 4: 'A',
                              5: 'E', 6: 'B'}

    sort_rule_flats = {'F': 6, 'C': 5, 'G': 4, 'D': 3, 'A': 2, 'E': 1,
                       'B': 0}
    sort_rule_notes_flats = {6: 'F', 5: 'C', 4: 'G', 3: 'D', 2: 'A',
                             1: 'E', 0: 'B'}

    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "symbtr.db")

    @classmethod
    def _write_lilypond(cls, measures, makam, usul, form, time_sigs,
                        keysig, render_metadata, work_title, composer,
                        lyricist):
        # connecting database, trying to get information for beams in lilypond
        conn = sqlite3.connect(os.path.join(cls.db_path))
        c = conn.cursor()

        # Initialize line number and mapping
        line = 0

        # getting headers
        if render_metadata:
            if lyricist and lyricist != '-':
                poet_str = """\n  poet = \"{0:s}\"""".format(lyricist)
                line += 1
            else:
                poet_str = ''

            metadata_str = """
  title = \"{0}\"
  composer = \"{1}\"
  piece = \"Makam: {2}, Form: {3}, Usul: {4}\"""".format(
                work_title, composer, form, makam, usul) + poet_str
            line += 3
        else:
            metadata_str = ''

        ly_stream = ["""
\\include "makam.ly" """ + """
\\header {
  tagline = \"\"""" + metadata_str +
                     """
}
{
  %\\override Score.SpacingSpanner.strict-note-spacing = ##t
  %\\set Score.proportionalNotationDuration = #(ly:make-moment 1/8)"""]
        line += 8

        # getting the components for the given usul
        c.execute('SELECT * FROM usul WHERE NAME="{0}"'.format(usul))
        data = c.fetchone()
        if data is None:
            c.execute('SELECT * FROM usul WHERE NAMEENG="{0}"'.format(
                usul.lower()))
            data = c.fetchone()

        # if beam information is exist
        if data is not None:
            if data[-1] is not None:
                strokes = data[-1].replace("+", " ")
                tmp_str = '''\n  \\set Staff.beatStructure = #\'({0})''' \
                    .format(strokes)
                ly_stream.append(tmp_str)
                line += 1

        # first time_signature
        ly_stream.append("\n  \\time")
        ly_stream.append("{0:s}/{1:s}".format(time_sigs[0]['beats'],
                                              time_sigs[0]['beat_type']))
        time_sigs.pop(0, None)  # remove the first time signature
        line += 1

        ly_stream.append("\n  \\clef treble")
        ly_stream.append("\n  \\set Staff.keySignature = #`(")
        line += 2

        accidentals_check = []
        rule = []
        for queue in keysig.keys():
            if cls._makam_accidentals[keysig[queue]][0] is "+":
                rule.append([cls.sort_rule_sharps[queue], 's'])
            else:
                rule.append([cls.sort_rule_flats[queue], 'f'])

        # sorting of key signatures
        temp_keysig = ""
        for queue in sorted(rule):
            if queue[1] is "s":
                key = cls.sort_rule_notes_sharps[queue[0]]
            else:
                key = cls.sort_rule_notes_flats[queue[0]]
            accidentals_check.append(key + cls._makam_accidentals[keysig[key].
                                     replace("+", "")])
            temp_keysig += "("
            temp_keysig += (cls._notes_western2lily[key.lower()] + " . ," +
                            cls._key_sig_accidentals[keysig[key]])
            temp_keysig += ") "

            ly_stream.append(temp_keysig)
            temp_keysig = ""

        ly_stream.append(")")

        mapping = []
        for mm, measure in enumerate(measures):
            ly_stream.append("\n  {{ % measure {0:d} beginning".format(mm + 1))
            line += 1

            # apply time signature change, if exists
            if mm in time_sigs.keys():
                # first time_signature
                ly_stream.append("\n    \\time")
                ly_stream.append("{0:s}/{1:s}".format(
                    time_sigs[mm]['beats'], time_sigs[mm]['beat_type']))
                line += 1

            tuplet = 0
            for note in measure:
                temp_note = "\n    "
                line += 1
                if note[6] is None:  # gracenote
                    # for now we display it as a 8th \grace
                    # TODO: Introduce other gracenotes such as \acciaccatura
                    # with the proper symbolic "duration"
                    temp_note += "\\grace "
                    note[6] = 0.5  # reminder: 4th note is 1
                    temp_dur = 4.0 / note[6]  # normal duration
                else:
                    temp_dur = 4.0 / note[6]  # normal duration

                # dotted
                if note[3] == 1:  # dot flag
                    temp_note += note[0]  # step
                    # accidental
                    temp_note += cls._accidentals[
                        str(note[2]).replace('+', '')]
                    temp_note += cls._octaves[note[1]]  # octave

                    temp_dur = temp_dur * 3.0 / 2
                    temp_note += str(int(temp_dur))
                    temp_note += "."
                elif note[4] == 1:  # tuplet flag
                    if tuplet == 0:
                        tuplet = 4
                        temp_note += "\\tuplet 3/2 {\n    "
                        line += 1
                    temp_note += '  '  # increase indentation
                    temp_note += note[0]  # step
                    # accidental
                    temp_note += cls._accidentals[
                        str(note[2]).replace('+', '')]
                    temp_note += cls._octaves[note[1]]  # octave

                    temp_dur = temp_dur * 2.0 / 3
                    temp_note += str(int(temp_dur))

                    tuplet -= 1
                else:  # normal
                    temp_note += note[0]
                    temp_note += cls._accidentals[
                        str(note[2]).replace('+', '')]
                    temp_note += cls._octaves[note[1]]
                    temp_note += str(int(temp_dur))
                if note[7]:
                    pos = len('    ')  # notes start with 4 spaces
                    mapping.append((note[7], pos, line))

                # lyrics
                if note[-1] is not "":
                    if len(note[-1]) > 1:
                        if note[-1][1].isupper() or note[-1][0].isdigit():
                            temp_note += (
                                '''^\\markup { \\left-align ''' +
                                '''{\\bold \\translate #'(1 . 0) \"''' +
                                ''.join(note[-1]).strip() + '''\"}}''')
                        else:
                            temp_note += (
                                '''_\\markup { \\center-align {\\smaller ''' +
                                '''\\translate #'(0 . -2.5) \"''' +
                                ''.join(note[-1]).strip() + '''\"}}''')
                    else:
                        temp_note += (
                            '''_\\markup { \\center-align {\\smaller ''' +
                            '''\\translate #'(0 . -2.5) \"''' +
                            ''.join(note[-1]).strip() + '''\"}}''')

                temp_note += ' % SymbTr-txt row index #' + str(note[7])
                if tuplet == 1:
                    temp_note += "\n    }"
                    tuplet = 0
                    line += 1

                ly_stream.append(temp_note)
            if mm == len(measures) - 1:
                ly_stream.append('''\n    \\bar \"|.\"''')  # closing bar
            ly_stream.append("\n  } % measure " + str(mm + 1) + " ending")
            line += 1

        ly_stream.append("\n}")  # close lilypond

        return ly_stream, mapping

    @classmethod
    def convert(cls, xml_in, ly_out=None, render_metadata=True):
        (measures, makam, usul, form, time_sigs, keysig, work_title,
         composer, poet) = MusicXMLReader.read(xml_in)

        ly_stream, mapping = cls._write_lilypond(
            measures, makam, usul, form, time_sigs, keysig,
            render_metadata, work_title, composer, poet)

        ly_stream = u''.join(ly_stream)
        # save to file
        if ly_out is not None:
            with open(ly_out, 'w') as outfile:
                outfile.write(ly_stream.encode('utf-8'))

        return ly_stream, mapping
