# koma definitions
N_NATURAL = 'natural'

# flats
B_KOMA = 'quarter-flat'  # 'flat-down'
B_BAKIYYE = 'slash-flat'
B_KMUCENNEP = 'flat'
B_BMUCENNEP = 'double-slash-flat'

# sharps
D_KOMA = 'quarter-sharp'  # quarter-sharp, SWAP 1ST AND 3RD SHARPS
D_BAKIYYE = 'sharp'
D_KMUCENNEP = 'slash-quarter-sharp'  # slash-quarter-sharp
D_BMUCENNEP = 'slash-sharp'

ALTER_VALUES = {'quarter-flat': "-0.5", 'slash-flat': None, 'flat': '-1',
                'double-slash-flat': None, 'quarter-sharp': '+0.5',
                'slash-sharp': None, 'sharp': "+1",
                'slash-quarter-sharp': None}

# section list
SECTION_LIST = ["1. HANE", "2. HANE", "3. HANE", "4. HANE", "TESLİM",
                "TESLİM ", "MÜLÂZİME", "SERHÂNE", "HÂNE-İ SÂNİ",
                "HÂNE-İ SÂLİS", "SERHANE", "ORTA HANE", "SON HANE",
                "1. HANEYE", "2. HANEYE", "3. HANEYE", "4. HANEYE",
                "KARAR", "1. HANE VE MÜLÂZİME", "2. HANE VE MÜLÂZİME",
                "3. HANE VE MÜLÂZİME", "4. HANE VE MÜLÂZİME",
                "1. HANE VE TESLİM", "2. HANE VE TESLİM",
                "3. HANE VE TESLİM", "4. HANE VE TESLİM", "ARANAĞME",
                "ZEMİN", "NAKARAT", "MEYAN", "SESLERLE NİNNİ",
                "OYUN KISMI", "ZEYBEK KISMI", "GİRİŞ SAZI",
                "GİRİŞ VE ARA SAZI", "GİRİŞ", "FİNAL", "SAZ", "ARA SAZI",
                "SUSTA", "KODA", "DAVUL", "RİTM", "BANDO", "MÜZİK",
                "SERBEST", "ARA TAKSİM", "GEÇİŞ TAKSİMİ", "KÜŞAT",
                "1. SELAM", "2. SELAM", "3. SELAM", "4. SELAM", "TERENNÜM"]


class Note:
    def __init__(self, info, verbose=None):
        # base attributes
        self.sira = None
        self.kod = None
        self.nota53 = None
        self.notaae = None
        self.koma53 = None
        self.komaae = None
        self.pay = None
        self.payda = None
        self.ms = None
        self.lns = None
        self.velon = None
        self.soz1 = None
        self.offset = None
        self.nofdivs = 0

        # xml attributes
        self.step = None  # get_pitch
        self.octave = None  # get_pitch
        self.duration = None
        self.type = None  # get_note_type
        self.accidental = None  # get_accidental
        self.alter = None  # get_accidental

        self.lyric = ''
        self.syllabic = None
        self.wordend = 0
        self.lineend = 0

        self.rest = 0  # get_rest
        self.grace = 0  # get_grace
        self.pregrace = 0
        self.dot = 0  # get_note_type
        self.tuplet = 0  # get_note_type
        self.tremolo = 0
        self.glissando = 0
        self.trill = 0
        self.mordent = 0
        self.invertedmordent = 0
        self.mordentlower = 0
        self.grupetto = 0
        self.littlenote = 0
        self.silentgrace = 0

        self.phraseend = 0

        self.graceerror = 0

        if verbose is None:
            verbose = False
        self.verbose = verbose
        self.fetchsymbtrinfo(info)

    def fetchsymbtrinfo(self, info):
        self.sira = info[0]
        self.kod = info[1]
        self.nota53 = info[2]
        self.notaae = info[3]
        self.koma53 = info[4]
        self.komaae = info[5]
        self.pay = info[6]
        self.payda = info[7]
        self.ms = info[8]
        self.lns = info[9]
        self.velon = info[10]
        self.soz1 = info[11]
        self.offset = info[12]
        if self.kod not in ['35', '51', '53', '54', '55']:
            self.get_rest()
            self.get_grace()
            if self.grace == 1 and self.pay != '0':
                self.graceerror = 1

                if self.verbose:
                    print("Warning: GraceError! pay and payda has been "
                          "changed.", self.sira, self.kod, self.pay)

                self.pay = '0'
                self.payda = '0'
            if self.rest == 0:
                self.get_pitch()
            # PAST NOTE: HAS TO FIX HERE (WHATEVER THERE IS TO BE FIXED)
            if self.grace == 0 and self.payda != '0' and self.kod != '0':
                self.get_note_type()
                self.get_accidental()
            self.get_word()

            # ornaments
            if self.kod == '1':
                self.littlenote = 1
            elif self.kod == '4':
                self.glissando = 1
            elif self.kod in ['7', '16']:
                self.tremolo = 1
            elif self.kod in ['12', '32']:
                self.trill = 1
            elif self.kod == '23':
                self.mordent = 1
            elif self.kod == '24':
                self.mordent = 1
                self.mordentlower = 1
            elif self.kod == '43':
                self.invertedmordent = 1
            elif self.kod == '44':
                self.invertedmordent = 1
                self.mordentlower = 1
            elif self.kod == '28':  # xml tag -> TURN
                self.grupetto = 1

        elif self.kod == '51':
            self.lyric = self.soz1

        elif self.kod == '53':  # phrase boundary
            self.phraseend = 1

    def get_rest(self):
        if self.kod == 0 or self.nota53 == "Es":
            self.rest = 1

    def get_grace(self):
        if self.kod == '8':
            self.grace = 1
        elif self.kod == '10':
            self.pregrace = 1
        elif self.kod == '11':
            self.silentgrace = 1

    def get_pitch(self):
        # try:
        self.step = self.notaae[0]
        self.octave = self.notaae[1]
        # except:
        #     raise ValueError('Pitch at line {0:s} with the value "{1:s}" '
        #                      'is invalid.'.format(self.sira, self.notaAE))

    def get_note_type(self):
        # print(self.sira, self.kod, "symbtrnote.get_note_type")
        temp_pay_payda = float(self.pay) / int(self.payda)

        temp_undotted = None
        if temp_pay_payda >= 1.0:
            self.type = 'whole'
            temp_undotted = 1.0
        elif 1.0 > temp_pay_payda >= 1.0 / 2:
            self.type = 'half'
            temp_undotted = 1.0 / 2
        elif 1.0 / 2 > temp_pay_payda >= 1.0 / 4:
            self.type = 'quarter'
            temp_undotted = 1.0 / 4
        elif 1.0 / 4 > temp_pay_payda >= 1.0 / 8:
            self.type = 'eighth'
            temp_undotted = 1.0 / 8
        elif 1.0 / 8 > temp_pay_payda >= 1.0 / 16:
            self.type = '16th'
            temp_undotted = 1.0 / 16
        elif 1.0 / 16 > temp_pay_payda >= 1.0 / 32:
            self.type = '32nd'
            temp_undotted = 1.0 / 32
        elif 1.0 / 32 > temp_pay_payda >= 1.0 / 64:
            self.type = '64th'
            temp_undotted = 1.0 / 64

        # check for tuplets
        if temp_pay_payda == 1.0 / 6:
            self.type = 'quarter'
            temp_undotted = 1.0 / 6
            self.tuplet = 1
        elif temp_pay_payda == 1.0 / 12:
            self.type = 'eighth'
            temp_undotted = 1.0 / 12
            self.tuplet = 1
        elif temp_pay_payda == 1.0 / 24:
            self.type = '16th'
            temp_undotted = 1.0 / 24
            self.tuplet = 1
        # end of tuplets

        if self.tuplet == 0:
            temp_remainder = temp_pay_payda - temp_undotted
            dot_val = temp_undotted / 2.0
            while temp_remainder > 0:
                # print(temp_pay_payda, temp_undotted, temp_remainder,
                # self.sira, self.type)
                self.dot += 1
                temp_remainder = temp_pay_payda - temp_undotted - dot_val
                dot_val += dot_val / 2
            if self.dot > 1 and 0:
                if self.verbose:
                    print("Dots! 1 or more. #ofDots:", self.dot, self.sira)
            # print(sira, temp_pay_payda, temp_undotted, dot_val,
            # temp_remainder)

    def get_accidental(self):
        acc = self.notaae[2:]
        if acc != '':
            if acc in ['#1', '#2']:
                self.accidental = D_KOMA
            elif acc in ['#3', '#4']:
                self.accidental = D_BAKIYYE
            elif acc in ['#5', '#6']:
                self.accidental = D_KMUCENNEP
            elif acc in ['#7', '#8']:
                self.accidental = D_BMUCENNEP
            elif acc in ['b1', 'b2']:
                self.accidental = B_KOMA
            elif acc in ['b3', 'b4']:
                self.accidental = B_BAKIYYE
            elif acc in ['b5', 'b6']:
                self.accidental = B_KMUCENNEP
            elif acc in ['b7', 'b8']:
                self.accidental = B_BMUCENNEP
            # print(self.sira)
            self.alter = ALTER_VALUES[self.accidental]

    def get_word(self):
        # we read the lyrics line even if the composition in instrumental to
        # write the secions and other structural info to the score

        # if self.soz1 not in SECTION_LIST:
        self.lyric = self.soz1
        self.syllabic = ""  # remove NoneType
        if '  ' in self.lyric:  # line endings
            self.lineend = 1
            self.wordend = 1
        elif ' ' in self.lyric:  # word endings
            self.wordend = 1

        if self.lineend or self.wordend:
            self.syllabic = "end"
