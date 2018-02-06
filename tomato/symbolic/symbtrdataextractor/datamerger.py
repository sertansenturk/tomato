import warnings


class DataMerger(object):
    @classmethod
    def merge(cls, data1, data2, verbose=True):
        """
        Merge the extracted score data from different formats (txt, mu2,
        MusicXML), the precedence goes to key value pairs in latter dicts.

        Parameters
        ----------
        data1 : dict
            The data extracted from SymbTr score
        data2 : dict
            The data extracted from SymbTr-mu2 file (or header)
        verbose : bool
            True to to print the warnings in the merge process, False otherwise

        Returns
        ----------
        dict
            Merged data extracted from the SymbTr scores
        """
        data1_dict = data1.copy()
        data2_dict = data2.copy()

        if 'work' in data1_dict.keys():
            data2_dict['work'] = data2_dict.pop('title')
        elif 'recording' in data1_dict.keys():
            data2_dict['recording'] = data2_dict.pop('title')
        else:
            if verbose:
                warnings.warn("There is no information about whether the "
                              "score is related to a composition or a "
                              "performance. The title key is skipped.",
                              stacklevel=2)
            data2_dict.pop('title')

        return cls._dictmerge(data1_dict, data2_dict)

    @classmethod
    def _dictmerge(cls, *data_dicts):
        """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.

        Parameters
        ----------
        *data_dicts : *dict
            Dictionaries of variable number to merge

        Returns
        ----------
        dict
            Merged dictionaries
        """
        result = {}
        for dictionary in data_dicts:
            dict_cp = dictionary.copy()
            for key, val in dict_cp.iteritems():
                if key not in result.keys():
                    result[key] = val
                elif not isinstance(result[key], dict):
                    cls._chk_dict_key_override(key, result, val)
                else:
                    result[key] = cls._dictmerge(result[key], val)

        return result

    @staticmethod
    def _chk_dict_key_override(key, result, val):
        if not result[key] == val:
            # overwrite
            warnings.warn(u'{0:s} already exists! Overwriting...'.format(key),
                          stacklevel=2)
            result[key] = val
