import logging
logging.basicConfig(level=logging.INFO)


class InstrumentationVoicing(object):
    """
    This class decide the voicing/instrumentation within an audio recording
    metadata from the artists fields
    """
    # Solo Vocal Without Accompaniment
    # There is only vocal and no instruments
    @staticmethod
    def solo_vocal_wo_acc(instrument_vocal_list):
        return (len(instrument_vocal_list) == 1 and
                instrument_vocal_list[0] == 'vocal')

    # Solo Vocal With Accompaniment
    # There is only one vocal and at least one instrument
    @staticmethod
    def solo_vocal_w_acc(instrument_vocal_list):
        return (len(instrument_vocal_list) > 1 and
                instrument_vocal_list.count('vocal') == 1)

    # Duet With Accompaniment
    # There are two vocals and at least one instrument
    @staticmethod
    def duet(instrument_vocal_list):
        return (instrument_vocal_list.count('vocal') == 2 and
                'choir_vocals' not in instrument_vocal_list)

    # Choir With Accompaniment
    # There are more than 2 vocals and at least one instrument
    @staticmethod
    def choir(instrument_vocal_list):
        return (instrument_vocal_list.count('vocal') > 2 or
                'choir_vocals' in instrument_vocal_list)

    # Solo Instrumental
    # There is no vocal and only one instrument
    @staticmethod
    def solo_instrumental(instrument_vocal_list):
        return (len(instrument_vocal_list) == 1 and
                instrument_vocal_list[0] in ['instrument', 'performer'])

    # Duo Instrumental
    # There is no vocal and only two instrument
    @staticmethod
    def duo_instrumental(instrument_vocal_list):
        return (len(instrument_vocal_list) == 2 and
                all(iv in ['instrument', 'performer']
                    for iv in instrument_vocal_list))

    # Trio Instrumental
    # There is no vocal and only three instrument
    @staticmethod
    def trio_instrumental(instrument_vocal_list):
        return (len(instrument_vocal_list) == 3 and
                all(iv in ['instrument', 'performer']
                    for iv in instrument_vocal_list))

    # Ensemble
    # There is no vocal and many instruments OR Orchestra relation
    @staticmethod
    def ensemble(instrument_vocal_list):
        return ('vocal' not in instrument_vocal_list and
                'choir_vocals' not in instrument_vocal_list and
                ('performing orchestra' in instrument_vocal_list or
                 len(instrument_vocal_list) > 3))

    @classmethod
    def check_instrumentation_voice(cls, instrument_vocal_list):
        # remove attributes, which are not about performance
        for ii, iv in reversed(list(enumerate(instrument_vocal_list))):
            if iv not in ['vocal', 'instrument', 'performing orchestra',
                          'performer', 'choir_vocals']:
                logging.info(u"{} is not related to performance.".format(iv))
                instrument_vocal_list.pop(ii)

        if cls.solo_instrumental(instrument_vocal_list):
            return "solo instrumental"
        elif cls.duo_instrumental(instrument_vocal_list):
            return "duo instrumental"
        elif cls.trio_instrumental(instrument_vocal_list):
            return "trio instrumental"
        elif cls.ensemble(instrument_vocal_list):
            return "ensemble instrumental"
        elif cls.solo_vocal_wo_acc(instrument_vocal_list):
            return "solo vocal without accompaniment"
        elif cls.solo_vocal_w_acc(instrument_vocal_list):
            return "solo vocal with accompaniment"
        elif cls.duet(instrument_vocal_list):
            return "duet"
        elif cls.choir(instrument_vocal_list):
            return "choir"
        else:
            assert False, "Unidentified voicing/instrumentation"

    @classmethod
    def get_voicing_instrumentation(cls, audio_meta):
        vocal_instrument = []
        for a in audio_meta['artists']:
            choir_bool = (a['type'] == 'vocal' and
                          'attribute-list' in a.keys() and
                          'choir_vocals' in a['attribute-list'])
            if choir_bool:
                vocal_instrument.append(a['attribute-list'])
            elif a['type'] in ['conductor']:
                pass
            else:
                vocal_instrument.append(a['type'])

        return cls.check_instrumentation_voice(vocal_instrument)
