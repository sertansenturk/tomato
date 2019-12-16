# -*- coding: utf-8 -*-
import copy
import os

from lxml import etree

from ...dataextractor import DataExtractor
from ...reader.mu2 import Mu2Reader
from .symbtrnote import Note

# koma definitions
n_natural = 'natural'

# flats
b_koma = 'quarter-flat'  # 'flat-down'
b_bakiyye = 'slash-flat'
b_kmucennep = 'flat'
b_bmucennep = 'double-slash-flat'

# sharps
d_koma = 'quarter-sharp'  # quarter-sharp    SWAP 1ST AND 3RD SHARPS
d_bakiyye = 'sharp'
d_kmucennep = 'slash-quarter-sharp'  # slash-quarter-sharp
d_bmucennep = 'slash-sharp'

# section list
section_list = [u"1. HANE", u"2. HANE", u"3. HANE", u"4. HANE", u"TESLİM",
                u"TESLİM ", u"MÜLÂZİME", u"SERHÂNE", u"HÂNE-İ SÂNİ",
                u"HÂNE-İ SÂLİS", u"SERHANE", u"ORTA HANE", u"SON HANE",
                u"1. HANEYE", u"2. HANEYE", u"3. HANEYE", u"4. HANEYE",
                u"KARAR", u"1. HANE VE MÜLÂZİME", u"2. HANE VE MÜLÂZİME",
                u"3. HANE VE MÜLÂZİME", u"4. HANE VE MÜLÂZİME",
                u"1. HANE VE TESLİM", u"2. HANE VE TESLİM",
                u"3. HANE VE TESLİM", u"4. HANE VE TESLİM", u"ARANAĞME",
                u"ZEMİN", u"NAKARAT", u"MEYAN", u"SESLERLE NİNNİ",
                u"OYUN KISMI", u"ZEYBEK KISMI", u"GİRİŞ SAZI",
                u"GİRİŞ VE ARA SAZI", u"GİRİŞ", u"FİNAL", u"SAZ",
                u"ARA SAZI", u"SUSTA", u"KODA", u"DAVUL", u"RİTM", u"BANDO",
                u"MÜZİK", u"SERBEST", u"ARA TAKSİM", u"GEÇİŞ TAKSİMİ",
                u"KÜŞAT", u"1. SELAM", u"2. SELAM", u"3. SELAM", u"4. SELAM",
                u"TERENNÜM"]

kodlist = []
koddict = dict()

printflag = 0

tuplet = 0
capitals = []

missing_usuls = []


def get_note_type(n_type, pay, payda):
    global tuplet

    # NEW PART FOR DOTTED NOTES
    temp_pay_payda = float(pay) / int(payda)
    temp_undotted = None
    if temp_pay_payda >= 1.0:
        n_type.text = 'whole'
        temp_undotted = 1.0
    elif 1.0 > temp_pay_payda >= 1.0 / 2:
        n_type.text = 'half'
        temp_undotted = 1.0 / 2
    elif 1.0 / 2 > temp_pay_payda >= 1.0 / 4:
        n_type.text = 'quarter'
        temp_undotted = 1.0 / 4
    elif 1.0 / 4 > temp_pay_payda >= 1.0 / 8:
        n_type.text = 'eighth'
        temp_undotted = 1.0 / 8
    elif 1.0 / 8 > temp_pay_payda >= 1.0 / 16:
        n_type.text = '16th'
        temp_undotted = 1.0 / 16
    elif 1.0 / 16 > temp_pay_payda >= 1.0 / 32:
        n_type.text = '32nd'
        temp_undotted = 1.0 / 32
    elif 1.0 / 32 > temp_pay_payda >= 1.0 / 64:
        n_type.text = '64th'
        temp_undotted = 1.0 / 64

    # check for tuplets
    if temp_pay_payda == 1.0 / 12:
        n_type.text = 'eighth'
        temp_undotted = 1.0 / 12
        tuplet += 1
    elif temp_pay_payda == 1.0 / 24:
        n_type.text = '16th'
        temp_undotted = 1.0 / 24
        tuplet += 1
    # end of tuplets

    # not tuplet, normal or dotted
    nofdots = 0
    timemodflag = 0
    if tuplet == 0:
        temp_remainder = temp_pay_payda - temp_undotted

        dot_val = temp_undotted / 2.0
        while temp_remainder > 0:
            nofdots += 1
            dot_val += dot_val / 2
            break

    # END OF NEW PART FOR DOTTED NOTES
    else:
        timemodflag = 1

    return timemodflag


def get_usul(usul):
    fpath = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'makams_usuls', 'usuls_v3_ANSI.txt')

    usul_id = []
    usul_name = []
    num_beats = []
    beat_type = []
    accents = []

    f = open(fpath, encoding='utf-8')

    while 1:
        temp_line = f.readline()

        if len(temp_line) == 0:
            break
        else:
            temp_line = temp_line.split('\t')
            temp_line.reverse()

            usul_id.append(temp_line.pop())
            usul_name.append(temp_line.pop())
            num_beats.append(temp_line.pop())
            beat_type.append(temp_line.pop())
            accents.append(temp_line.pop())

    f.close()
    # eof filepath read
    '''
    print(usulID[usulID.index(usul)])
    print(usulName)
    print(nofBeats[usulID.index(usul)])
    print(beatType[usulID.index(usul)])
    print(accents)
    print(len(usulID),len(usulName),len(nofBeats),len(beatType),len(accents))
    '''

    return int(num_beats[usul_id.index(usul)]), int(
        beat_type[usul_id.index(usul)])


def get_accidental_name(alter):
    acc_name = n_natural
    if alter in ['+1', '+2']:
        acc_name = d_koma
    elif alter in ['+3', '+4']:
        acc_name = d_bakiyye
    elif alter in ['+5', '+6']:
        acc_name = d_kmucennep
    elif alter in ['+7', '+8']:
        acc_name = d_bmucennep
    elif alter in ['-1', '-2']:
        acc_name = b_koma
    elif alter in ['-3', '-4']:
        acc_name = b_bakiyye
    elif alter in ['-5', '-6']:
        acc_name = b_kmucennep
    elif alter in ['-7', '-8']:
        acc_name = b_bmucennep

    return acc_name


def get_key_signature(piecemakam, keysig):
    makam_tree = etree.parse(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'makams_usuls', 'Makamlar.xml'))

    xpression = '//dataroot/Makamlar[makam_adi= $makam]/'
    makam_ = piecemakam

    key_signature = []
    solfege_letter_dict = {'La': 'A', 'Si': 'B', 'Do': 'C', 'Re': 'D',
                           'Mi': 'E', 'Fa': 'F', 'Sol': 'G'}

    for i in range(1, 10):
        try:
            key_signature.append((makam_tree.xpath(
                xpression + 'Donanim-' + str(i), makam=makam_))[0].text)
            for key, value in solfege_letter_dict.items():
                key_signature[-1] = key_signature[-1].replace(key, value)
        except IndexError:  # end of the accidentals in the key signature
            continue
        except AttributeError:
            continue

    key_signature.reverse()

    while len(key_signature) > 0:
        temp_key = key_signature.pop()
        if temp_key is not None:
            temp_key = temp_key.replace('#', '+')
            temp_key = temp_key.replace('b', '-')

            keystep = etree.SubElement(keysig, 'key-step')
            keystep.text = temp_key[0]
            # ''' alteration is not working for microtones
            keyalter = etree.SubElement(keysig, 'key-alter')
            keyalter.text = temp_key[-2:]
            # '''
            keyaccidental = etree.SubElement(keysig, 'key-accidental')
            keyaccidental.text = get_accidental_name(temp_key[-2:])


class SymbTrScore(object):
    def __init__(self, txtpath, mu2path, symbtrname='', mbid_url='',
                 verbose=None):
        self.txtpath = txtpath  # filepath for the txt score
        self.mu2path = mu2path  # filepath for the mu2 score; used for
        # obtaining the symbtr from its header

        # musicbrainz unique identifier (there can be more than one MBID)
        try:  # python 2
            self.mbid_url = [mbid_url] if isinstance(mbid_url, basestring) \
                else mbid_url
        except NameError:  # python
            self.mbid_url = [mbid_url] if isinstance(mbid_url, str) \
                else mbid_url
        self.siraintervals = []

        if verbose is None:
            verbose = False
        self.verbose = verbose

        if not symbtrname:
            self.symbtrname = os.path.splitext(
                os.path.basename(self.txtpath))[0]
        else:
            self.symbtrname = symbtrname

        # piece attributes
        self.makam = ""
        self.form = ""
        self.usul = ""
        self.name = ""
        self.composer = ""
        self.lyricist = ""
        self.mu2header = dict()
        self.mblink = []

        self.keysignature = []
        self.timesignature = []

        self.notes = []
        self.notecount = 0
        self.measures = []
        self.tempo = None
        self.mu2beatnumber = None
        self.mu2beattype = None

        self.tuplet = 0
        self.tupletseq = []

        self.score = None
        self.sections = []
        self.scorenotes = []
        self.sectionsextracted = dict()
        self.capitals = []
        self.phraseboundaryinfo = 0
        self.subdivisionthreshold = 0

        (self.makam, self.form, self.usul, self.name, self.composer,
         self.mu2header, self.mu2composer, self.mu2lyricist,
         self.mu2beatnumber, self.mu2beattype, self.notecount) = \
            self.readsymbtr()  # read symbtr txt file

        self.symbt2xmldict = dict()

        # xml attribute flags
        self.xmlnotationsflag = 0
        self.xmlgraceslurflag = 0
        self.xmlglissandoflag = 0

    def printnotes(self):
        for e in self.notes:
            # pass
            print(vars(e))

    def sectionextractor(self):
        extractor = DataExtractor(
            extract_all_labels=True, print_warnings=False)
        data, is_data_valid = extractor.extract(
            self.txtpath, symbtr_name=self.symbtrname)

        mu2_header, header_row, is_header_valid = \
            Mu2Reader.read_header(self.mu2path, symbtr_name=self.symbtrname)

        # data = extractor.merge(txtdata, Mu2header)
        for item in data['sections']:
            self.sectionsextracted[item['start_note']] = item['name']

        mu2title = mu2_header['title']['mu2_title']
        if mu2title is None:
            mu2title = (mu2_header['makam']['mu2_name'] +
                        mu2_header['usul']['mu2_name'])

        mu2composer = mu2_header['composer']['mu2_name']
        mu2lyricist = mu2_header['lyricist']['mu2_name']
        mu2beatnumber = mu2_header['usul']['number_of_pulses']
        mu2beattype = mu2_header['usul']['mertebe']

        return (mu2_header, mu2composer, mu2lyricist, mu2beatnumber,
                mu2beattype, mu2title)

    def readsymbtr(self):
        finfo = self.symbtrname.split('--')
        finfo[-1] = finfo[-1][:-4]

        makam = finfo[0]
        form = finfo[1]
        usul = finfo[2]

        composer = finfo[4]
        composer = composer.replace('_', ' ').title()

        mu2header, mu2composer, mu2lyricist, mu2beatnumber, mu2beattype, \
            name = self.sectionextractor()

        self.readsymbtrlines()
        notecount = len(self.notes)

        return (makam, form, usul, name, composer, mu2header, mu2composer,
                mu2lyricist, mu2beatnumber, mu2beattype, notecount)

    def readsymbtrlines(self):
        global kodlist, koddict

        # read operation
        f = open(self.txtpath, encoding='utf-8')
        f.readline()
        while 1:
            temp_line = f.readline()  # column headers line
            if len(temp_line) == 0:
                break
            else:
                temp_line = temp_line.split('\t')
                # NOTE CLASS
                self.notes.append(
                    Note(temp_line, verbose=self.verbose))

                if self.notes[-1].kod not in ['51']:
                    if self.notes[-1].pay in ['5', '10']:  # seperating notes
                        temppay = int(self.notes[-1].pay)

                        del self.notes[-1]
                        firstpart = temppay * 2 / 5
                        lastpart = temppay - firstpart

                        temp_line[6] = str(firstpart)
                        self.notes.append(Note(
                            temp_line, verbose=self.verbose))
                        temp_line[6] = str(lastpart)
                        temp_line[11] = '_'
                        self.notes.append(Note(
                            temp_line, verbose=self.verbose))
                    elif self.notes[-1].pay in ['9', '11']:
                        temppay = int(self.notes[-1].pay)
                        del self.notes[-1]

                        temp_line[6] = str(3)
                        self.notes.append(Note(
                            temp_line, verbose=self.verbose))
                        temp_line[6] = str(temppay - 3)
                        temp_line[11] = '_'
                        self.notes.append(Note(
                            temp_line, verbose=self.verbose))

                # removing rests with 0 duration
                if self.notes[-1].rest == 1 and self.notes[-1].pay == '0':
                    if self.verbose:
                        print("Warning! Note deleted. Rest with Pay:0. Sira:",
                              self.notes[-1].sira)
                    del self.notes[-1]
                # DONE READING

                lastnote = self.notes[-1]
                if lastnote.graceerror == 1 and self.verbose:
                    print("\tgrace error:", lastnote.sira, lastnote.kod,
                          lastnote.pay, lastnote.payda)

                if lastnote.kod in koddict:
                    koddict[lastnote.kod] += 1
                else:
                    koddict[lastnote.kod] = 1

                self.scorenotes.append(self.notes[-1].kod)
                kodlist.append(self.scorenotes[-1])

        kodlist = list(set(kodlist))
        if '53' in self.scorenotes:
            self.phraseboundaryinfo = 1

        f.close()

    def symbtrtempo(self, pay1, ms1, payda1, pay2, ms2, payda2):
        try:
            bpm = 60000 * 4 * int(pay1) / (int(ms1) * int(payda1))
        except ZeroDivisionError:
            bpm = 60000 * 4 * int(pay2) / (int(ms2) * int(payda2))
        self.tempo = bpm
        return bpm

    @staticmethod
    def addwordinfo(xmllyric, templyric, word, e):
        # lyrics word information
        if (len(templyric) > 0 and templyric != "." and
                templyric not in section_list):
            syllabic = etree.SubElement(xmllyric, 'syllabic')
            if e.syllabic is not None and word == 1:
                syllabic.text = "end"
                word = 0
            else:
                if word == 0 and (e.wordend or e.lineend):
                    syllabic.text = "single"
                    word = 0
                elif word == 0:
                    syllabic.text = "begin"
                    word = 1
                elif word == 1:
                    syllabic.text = "middle"
        return word

    @staticmethod
    def addduration(num_divs, xmlduration, e):
        temp_duration = int(num_divs * 4 * float(e.pay) / float(e.payda))
        xmlduration.text = str(temp_duration)

        return temp_duration  # duration calculation	UNIVERSAL

    def addaccidental(self, xmlnote, xmlpitch, e):
        if e.accidental not in [None]:
            # accidental XML create
            accidental = etree.SubElement(xmlnote, 'accidental')
            accidental.text = e.accidental
            '''
            alter = etree.SubElement(pitch, 'alter')
            if int(acc) > 0:
                alter.text = '1'
            else:
                alter.text = '-1'
            '''
            self.addalter(xmlpitch, e)

    @staticmethod
    def addalter(xmlpitch, e):
        if e.alter is not None:
            alter = etree.SubElement(xmlpitch, 'alter')
            alter.text = e.alter

    def adddot(self, xmlnote, e):
        # adding dots
        for i in range(0, e.dot):
            etree.SubElement(xmlnote, 'dot')
            if self.verbose:
                print("DOT ADDED", e.sira)

    def addtuplet(self, xmlnote, e):
        global tuplet
        tuplet += 1

        self.tupletseq.append(int(e.payda))
        if tuplet > 1:
            if self.tupletseq[-2] != self.tupletseq[-1]:
                tuplet += 1

        time_mod = etree.SubElement(xmlnote, 'time-modification')
        act_note = etree.SubElement(time_mod, 'actual-notes')
        act_note.text = '3'
        norm_note = etree.SubElement(time_mod, 'normal-notes')
        norm_note.text = '2'

        xmlnotat = etree.SubElement(xmlnote, 'notations')
        self.xmlnotationsflag = 1

        if self.verbose:
            print("Tuplet added.", tuplet, e.tuplet, e.sira)
        # check for tuplets
        if tuplet == 1:
            tupletstart = etree.SubElement(xmlnotat, 'tuplet')
            tupletstart.set('type', 'start')
            tupletstart.set('bracket', 'yes')
        elif tuplet == 2:
            pass
        elif tuplet == 3:
            tupletstop = etree.SubElement(xmlnotat, 'tuplet')
            tupletstop.set('type', 'stop')
            # tupl.set('bracket', 'yes')
            tuplet = 0
            if self.verbose:
                print("Tuplet sequence:", self.tupletseq)
            self.tupletseq = []

        return xmlnotat

    @staticmethod
    def addtimemodification(note):
        global tuplet
        time_mod = etree.SubElement(note, 'time-modification')
        act_note = etree.SubElement(time_mod, 'actual-notes')
        act_note.text = '3'
        norm_note = etree.SubElement(time_mod, 'normal-notes')
        norm_note.text = '2'

        if tuplet == 1:
            notat = etree.SubElement(note, 'notations')
            tupletstart = etree.SubElement(notat, 'tuplet')
            tupletstart.set('type', 'start')
            tupletstart.set('bracket', 'yes')
        elif tuplet == 3:
            notat = etree.SubElement(note, 'notations')
            tupletstop = etree.SubElement(notat, 'tuplet')
            tupletstop.set('type', 'stop')
            # tupl.set('bracket', 'yes')
            tuplet = 0

    def addtremolo(self, xmlnotations, e):
        xmlornaments = etree.SubElement(xmlnotations, 'ornaments')
        xmltremolo = etree.SubElement(xmlornaments, 'tremolo')
        xmltremolo.set('type', 'single')
        xmltremolo.text = "2"
        if self.verbose:
            print("Tremolo added.", e.sira, e.kod)

    def addglissando(self, xmlnotations, e):
        if self.xmlglissandoflag == 1:
            xmlglissando = etree.SubElement(xmlnotations, 'glissando')
            xmlglissando.set('type', 'stop')
            self.xmlglissandoflag = 0
            if self.verbose:
                print("Glissando stop. Flag:", self.xmlglissandoflag, e.sira,
                      e.kod, e.lyric)
        if e.glissando == 1:
            xmlglissando = etree.SubElement(xmlnotations, 'glissando')
            xmlglissando.set('line-type', 'wavy')
            xmlglissando.set('type', 'start')
            self.xmlglissandoflag = 1

            if self.verbose:
                print("Glissando start. Flag:", self.xmlglissandoflag, e.sira,
                      e.kod, e.lyric)

    def addtrill(self, xmlnotations, e):
        xmlornaments = etree.SubElement(xmlnotations, 'ornaments')
        xmltrill = etree.SubElement(xmlornaments, 'trill-mark')
        xmltrill.set('placement', 'above')

        if self.verbose:
            print("Trill added.", e.sira, e.kod)

    def addgrace(self, xmlnote):
        grace = etree.SubElement(xmlnote, 'grace')  # note pitch XML create
        if self.xmlgraceslurflag > 0:
            grace.set('steal-time-previous', '10')
        else:
            grace.set('steal-time-following', '10')

    def addgraceslur(self, xmlnotations):
        if self.xmlgraceslurflag == 2:
            xmlgraceslur = etree.SubElement(xmlnotations, 'slur')
            xmlgraceslur.set('type', 'start')
            self.xmlgraceslurflag = 1
        else:
            xmlgraceslur = etree.SubElement(xmlnotations, 'slur')
            xmlgraceslur.set('type', 'stop')
            self.xmlgraceslurflag = 0

        if self.verbose:
            print("Grace slur flag:", self.xmlgraceslurflag)

    def addmordent(self, xmlnotations, e):
        xmlornaments = etree.SubElement(xmlnotations, 'ornaments')
        xmlmordent = etree.SubElement(xmlornaments, 'mordent')
        xmlmordent.set('placement', 'above')

        if e.mordentlower == 1:
            self.addlowermordent(xmlmordent)
            # pass

        if self.verbose:
            print("Mordent added.", e.sira, e.kod)

    def addinvertedmordent(self, xmlnotations, e):
        xmlornaments = etree.SubElement(xmlnotations, 'ornaments')
        xmlinvertedmordent = etree.SubElement(xmlornaments, 'inverted-mordent')
        xmlinvertedmordent.set('placement', 'below')

        if e.mordentlower == 1:
            self.addlowermordent(xmlinvertedmordent)
            # pass

        if self.verbose:
            print("Inverted Mordent added.", e.sira, e.kod)

    def addgrupetto(self, xmlnotations, e):
        xmlornaments = etree.SubElement(xmlnotations, 'ornaments')
        etree.SubElement(xmlornaments, 'turn')

        if self.verbose:
            print("Grupetto added.", e.sira, e.kod)

    @staticmethod
    def addlowermordent(xmlmordent):
        xmlmordent.set('approach', 'below')
        xmlmordent.set('departure', 'above')

    def usulchange(self, measure, e, tempatts, nof_divs):
        temp_num_beats = int(e.pay)
        temp_beat_type = int(e.payda)
        measure_len = temp_num_beats * nof_divs * (4 / float(temp_beat_type))

        time = etree.SubElement(tempatts, 'time')
        num_beats = etree.SubElement(time, 'beats')
        beat_type = etree.SubElement(time, 'beat-type')
        num_beats.text = str(temp_num_beats)
        beat_type.text = str(temp_beat_type)

        # 1st measure direction: usul and makam info
        # tempo(metronome)
        direction = etree.SubElement(measure, 'direction')
        direction.set('placement', 'above')
        direction_type = etree.SubElement(direction, 'direction-type')

        # usul and tempo info
        tempindex = self.notes.index(e)
        tempo = self.symbtrtempo(
            self.notes[tempindex + 1].pay,
            float(self.notes[tempindex + 1].ms) - float(e.ms),
            self.notes[tempindex + 1].payda, self.notes[tempindex + 2].pay,
            float(self.notes[tempindex + 2].ms) -
            float(self.notes[tempindex + 1].ms),
            self.notes[tempindex + 2].payda)

        xmlmetronome = etree.SubElement(direction_type, 'metronome')
        xmlbeatunit = etree.SubElement(xmlmetronome, 'beat-unit')
        xmlbeatunit.text = 'quarter'
        xmlperminute = etree.SubElement(xmlmetronome, 'per-minute')
        xmlperminute.text = str(tempo)

        direction_type = etree.SubElement(direction, 'direction-type')
        words = etree.SubElement(direction_type, 'words')
        words.set('default-y', '35')
        if e.lyric:
            words.text = 'Usul: ' + e.lyric.title()

        sound = etree.SubElement(direction, 'sound')
        sound.set('tempo', str(tempo))
        if self.verbose:
            print("Tempo change ok.", e.sira, self.notes[tempindex + 1].sira)

        return measure_len

    @staticmethod
    def setsection(tempmeasurehead, lyric, templyric):
        if templyric != "SAZ":
            tempheadsection = tempmeasurehead.find(".//lyric")
        else:
            tempheadsection = lyric
        tempheadsection.set('name', templyric)

    @staticmethod
    def countcapitals(string):
        global capitals
        if string.isupper():
            capitals.append(string)

    def convertsymbtr2xml(self, verbose=None):
        if verbose is not None:
            self.verbose = verbose

        outkoddict = dict((e, 0) for e in kodlist)
        global tuplet
        tuplet = 0

        # CREATE MUSIC XML
        # init
        self.score = etree.Element("score-partwise")  # score-partwise
        self.score.set('version', '3.0')

        # work-title
        work = etree.SubElement(self.score, 'work')
        work_title = etree.SubElement(work, 'work-title')
        work_title.text = self.name.title()

        # identification
        xmlidentification = etree.SubElement(self.score, 'identification')
        xmlcomposer = etree.SubElement(xmlidentification, 'creator')
        xmlcomposer.set('type', 'composer')
        xmlcomposer.text = self.mu2composer
        if len(self.mu2lyricist) > 0:
            xmllyricist = etree.SubElement(xmlidentification, 'creator')
            xmllyricist.set('type', 'poet')
            xmllyricist.text = self.mu2lyricist

        xmlencoding = etree.SubElement(xmlidentification, 'encoding')
        xmlencoder = etree.SubElement(xmlencoding, 'encoder')
        xmlencoder.text = 'Burak Uyar'
        xmlsoftware = etree.SubElement(xmlencoding, 'software')
        xmlsoftware.text = 'https://github.com/burakuyar/MusicXMLConverter'

        for idlink in self.mbid_url:
            xmlrelation = etree.SubElement(xmlidentification, 'relation')
            xmlrelation.text = idlink

        # part-list
        part_list = etree.SubElement(self.score, 'part-list')
        score_part = etree.SubElement(part_list, 'score-part')
        score_part.set('id', 'P1')
        part_name = etree.SubElement(score_part, 'part-name')
        part_name.text = 'Music'

        # part1
        p1 = etree.SubElement(self.score, 'part')
        p1.set('id', 'P1')

        # measures array
        measure = []
        i = 1  # measure counter
        measure_sum = 0
        subdivisioncounter = 0
        measuredelim = "-"

        # part1 measure1
        measure.append(etree.SubElement(p1, 'measure'))
        measure[-1].set('number', str(i) + measuredelim +
                        str(subdivisioncounter))

        # 1st measure direction: usul and makam info
        # tempo(metronome)
        direction = etree.SubElement(measure[-1], 'direction')
        direction.set('placement', 'above')
        direction_type = etree.SubElement(direction, 'direction-type')

        # usul and makam info

        # tempo info
        tempo = self.symbtrtempo(
            self.notes[1].pay, self.notes[1].ms, self.notes[1].payda,
            self.notes[2].pay, self.notes[2].ms, self.notes[2].payda)

        xmlmetronome = etree.SubElement(direction_type, 'metronome')
        xmlbeatunit = etree.SubElement(xmlmetronome, 'beat-unit')
        xmlbeatunit.text = 'quarter'
        xmlperminute = etree.SubElement(xmlmetronome, 'per-minute')
        xmlperminute.text = str(tempo)

        # add text to usul with time signature
        direction_type = etree.SubElement(direction, 'direction-type')
        words = etree.SubElement(direction_type, 'words')
        words.set('default-y', '35')
        # add a space in the end, because metronome will be rendered right next
        # to this text
        words.text = 'Makam: ' + self.mu2header['makam']['mu2_name'] + \
                     ', Form: ' + self.mu2header['form']['mu2_name'] + \
                     ', Usul: ' + self.mu2header['usul']['mu2_name'] + ' '

        sound = etree.SubElement(direction, 'sound')
        sound.set('tempo', str(tempo))

        num_divs = 96
        if self.usul not in ['serbest', 'belirsiz']:
            temp_num_beats = self.mu2beatnumber
            temp_beat_type = self.mu2beattype

            measure_len = (temp_num_beats * num_divs *
                           4 / float(temp_beat_type))

            if temp_num_beats >= 20:
                if temp_num_beats % 4 == 0:
                    self.subdivisionthreshold = \
                        measure_len / (temp_num_beats / 4)
                elif temp_num_beats % 2 == 0:
                    self.subdivisionthreshold = \
                        measure_len / (temp_num_beats / 2)
                elif temp_num_beats % 3 == 0:
                    self.subdivisionthreshold = \
                        measure_len / (temp_num_beats / 3)

            if self.verbose:
                print("After long usul check:", measure_len,
                      self.subdivisionthreshold, temp_num_beats)

        else:
            temp_num_beats = ''
            temp_beat_type = ''
            measure_len = 1000

        # ATTRIBUTES
        atts1 = etree.SubElement(measure[-1], 'attributes')
        divs1 = etree.SubElement(atts1, 'divisions')
        divs1.text = str(num_divs)

        # key signature
        keysig = etree.SubElement(atts1, 'key')
        get_key_signature(self.makam, keysig)

        time = etree.SubElement(atts1, 'time')
        if self.usul in ['serbest', 'belirsiz']:
            etree.SubElement(time, 'senza-misura')
        else:
            beats = etree.SubElement(time, 'beats')
            beat_type = etree.SubElement(time, 'beat-type')
            beats.text = str(temp_num_beats)
            beat_type.text = str(temp_beat_type)

        # LOOP FOR NOTES
        # notes
        word = 0
        # sentence = 0
        # tempsection = 0
        # graceflag = 0
        tempatts = ""
        startindex = None
        # tempmeasurehead = measure[-1]

        if self.phraseboundaryinfo == 1:
            xmlgrouping = etree.SubElement(measure[-1], 'grouping')
            xmlgrouping.set('type', 'start')
            etree.SubElement(xmlgrouping, 'feature')

        for e in self.notes:
            tempkod = e.kod
            tempsira = e.sira
            temppayda = e.payda
            tempstep = e.step
            tempoct = e.octave
            templyric = e.lyric

            self.xmlnotationsflag = 0
            if tempkod not in ['35', '50', '51', '53', '54', '55']:
                if not startindex:
                    startindex = tempsira
                # note UNIVERSAL
                xmlnote = etree.SubElement(measure[-1], 'note')
                self.symbt2xmldict[e.sira] = xmlnote
                xmlnote.append(etree.Comment('symbtr_txt_note_index ' +
                                             e.sira))

                # kods cannot mapped to musicxml
                if e.littlenote == 1:
                    xmlnote.append(etree.Comment(
                        'Warning! SymbTr_Kod: 1 Little note.  MusicXML schema '
                        'does not have a appropriate mapping, treating the '
                        'note as a normal note'))
                if e.silentgrace == 1:
                    xmlnote.append(etree.Comment(
                        'Warning! SymbTr_Kod: 11 Silent grace. MusicXML '
                        'schema does not have a appropriate mapping, '
                        'treating the note as a normal note'))

                if e.grace == 1:
                    outkoddict['8'] += 1
                    self.addgrace(xmlnote)
                    if self.xmlgraceslurflag == 0:
                        self.xmlgraceslurflag = 2
                elif e.pregrace == 1:
                    outkoddict['10'] += 1
                    self.xmlgraceslurflag = 2
                else:
                    pass

                if e.rest == 0:
                    outkoddict['9'] += 1
                    # note pitch XML create
                    pitch = etree.SubElement(xmlnote, 'pitch')
                else:
                    outkoddict['9'] += 1
                    # note rest XML create	REST
                    etree.SubElement(xmlnote, 'rest')

                if e.grace == 0:
                    # note duration XML create	UNIVERSAL
                    xmlduration = etree.SubElement(xmlnote, 'duration')
                    # note type XML create	UNIVERSAL
                    xmltype = etree.SubElement(xmlnote, 'type')

                if int(temppayda) == 0:
                    temp_duration = 0
                else:
                    # duration calculation UNIVERSAL
                    temp_duration = self.addduration(num_divs, xmlduration, e)
                    xmltype.text = e.type
                    self.adddot(xmlnote, e)

                if e.rest == 0:
                    # note pitch step XML create
                    step = etree.SubElement(pitch, 'step')
                    step.text = tempstep  # step val #XML assign

                    self.addaccidental(xmlnote, pitch, e)

                    # note pitch octave XML create
                    octave = etree.SubElement(pitch, 'octave')
                    octave.text = tempoct  # octave val XML assign

                if e.tuplet == 1:
                    outkoddict['9'] += 1
                    xmlnotations = self.addtuplet(xmlnote, e)
                    if e.tremolo == 1 or e.glissando == 1:
                        if self.verbose:
                            print("Tuplet with tremolo or glissando.")
                if e.tremolo == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for tremolo.")
                    self.addtremolo(xmlnotations, e)
                if e.glissando == 1 or self.xmlglissandoflag == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for glissando.")
                    self.addglissando(xmlnotations, e)
                if e.trill == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for trill.")
                    self.addtrill(xmlnotations, e)
                if e.mordent == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for mordent.")
                    self.addmordent(xmlnotations, e)
                if e.invertedmordent == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for inverted mordent.",
                                  e.sira, e.kod, e.invertedmordent)
                    self.addinvertedmordent(xmlnotations, e)
                if e.grupetto == 1:
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for grupetto/turn.",
                                  e.sira, e.kod, e.invertedmordent)
                    self.addgrupetto(xmlnotations, e)

                if self.xmlgraceslurflag > 0 and 0:  # disabled temporarily
                    if xmlnote.find('notations') is None:
                        xmlnotations = etree.SubElement(xmlnote, 'notations')
                        if self.verbose:
                            print("Notations is added for grace.")
                    self.addgraceslur(xmlnotations)

                # LYRICS PART
                xmllyric = etree.SubElement(xmlnote, 'lyric')
                # word keeps the status of current syllable
                word = self.addwordinfo(xmllyric, templyric, word, e)
                # current lyric text
                xmltext = etree.SubElement(xmllyric, 'text')
                xmltext.text = templyric

                self.countcapitals(templyric)

                if e.lineend == 1:
                    etree.SubElement(xmllyric, 'end-line')

                # section information
                # instrumental pieces and pieces with section keywords
                if int(tempsira) in self.sectionsextracted.keys():
                    # self.setsection(tempmeasurehead, xmllyric, templyric)
                    tempsection = self.sectionsextracted[int(tempsira)]
                    xmllyric.set('name', tempsection)
                    self.sections.append(tempsection)

                measure_sum += temp_duration
                # NEW MEASURE except it is the end of the piece
                if measure_sum >= measure_len and e is not self.notes[-1]:
                    subdivisioncounter = 0
                    i = int(i + 1)
                    measure.append(etree.SubElement(p1, 'measure'))
                    measure[-1].set('number', str(i) + measuredelim +
                                    str(subdivisioncounter))
                    tempatts = etree.SubElement(measure[-1], 'attributes')
                    measure_sum = 0

                    self.siraintervals.append({"start": startindex,
                                               "end": tempsira})
                    startindex = None
                    # eof notes
                # disabled temporarily
                elif self.subdivisionthreshold != 0 and measure_sum % \
                        self.subdivisionthreshold == 0 and 0:
                    subdivisioncounter += 1
                    measure.append(etree.SubElement(p1, 'measure'))
                    measure[-1].set('number', str(i) + measuredelim +
                                    str(subdivisioncounter))
                    tempatts = etree.SubElement(measure[-1], 'attributes')

                    xmlbarline = etree.SubElement(measure[-1], 'barline')
                    xmlbarline.set('location', 'left')
                    xmlbarstyle = etree.SubElement(xmlbarline, 'bar-style')
                    xmlbarstyle.text = 'dashed'

            elif tempkod == '51':
                if e.sira == '1':
                    if self.verbose:
                        print("Initial usul is already set.")
                else:
                    try:
                        measure_len = self.usulchange(
                            measure[-1], e, tempatts, num_divs)
                    except IndexError:
                        if self.verbose:
                            print('Kod', tempkod, 'but no time information.',
                                  e.sira, e.kod)

            elif tempkod == '50':
                if self.verbose:
                    print("makam change", self.txtpath, tempsira)

            elif tempkod == '35':
                if self.verbose:
                    print("Measure repetition.", e.sira)
                p1.remove(measure[-1])  # remove empty measure
                del measure[-1]

                xmeasure = copy.deepcopy(measure[-1])
                xmeasure.set('number', str(i))
                if xmeasure.find('direction') is not None:
                    xmeasure.remove(xmeasure.find('direction'))
                if xmeasure.find('attributes') is not None:
                    tempatts = xmeasure.find('attributes')
                    tempatts.clear()

                # this part will be active after musescore supports measure
                # repetition
                '''
                xmlmeasurestyle = etree.SubElement(tempatts, 'measure-style')
                xmlmeasurerepeat = etree.SubElement(xmlmeasurestyle,
                                                    'measure-repeat')
                xmlmeasurerepeat.set('type', 'start')
                xmlmeasurerepeat.text = '1'
                '''

                p1.append(xmeasure)  # add copied measure to the score
                measure[-1] = xmeasure

                i += 1
                measure.append(etree.SubElement(p1, 'measure'))
                measure[-1].set('number', str(i))
                tempatts = etree.SubElement(measure[-1], 'attributes')
                measure_sum = 0

            elif tempkod == '53':  # phrase boundaries
                xmlgrouping = etree.SubElement(measure[-1], 'grouping')
                xmlgrouping.set('type', 'stop')
                xmlfeature = etree.SubElement(xmlgrouping, 'feature')
                xmlfeature.set('type', 'phrase')

                if self.notes.index(e) != len(self.notes) - 1:
                    xmlgrouping = etree.SubElement(measure[-1], 'grouping')
                    xmlgrouping.set('type', 'start')
                    xmlfeature = etree.SubElement(xmlgrouping, 'feature')
                    xmlfeature.set('type', 'phrase')

            elif tempkod == '54':  # flavors
                xmlgrouping = etree.SubElement(measure[-1], 'grouping')
                xmlgrouping.set('type', 'start')
                xmlfeature = etree.SubElement(xmlgrouping, 'feature')
                xmlfeature.set('type', 'flavor')
            elif tempkod == '55':  # flavours
                xmlgrouping = etree.SubElement(measure[-1], 'grouping')
                xmlgrouping.set('type', 'stop')
                xmlfeature = etree.SubElement(xmlgrouping, 'feature')
                xmlfeature.set('type', 'flavor')

        return self.getxmlstr()

    def getxmlstr(self):
        temp_doctype = '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD ' \
                       'MusicXML 3.0 Partwise//EN" ' \
                       '"http://www.musicxml.org/dtds/partwise.dtd">'
        return etree.tostring(
            self.score, pretty_print=True, xml_declaration=True,
            encoding="UTF-8", standalone=False,
            doctype=temp_doctype)

    def get_measure_bounds(self):
        return self.siraintervals

    def writexml(self, outpath):
        f = open(outpath, 'wb')
        f.write(self.getxmlstr())
        f.close()
