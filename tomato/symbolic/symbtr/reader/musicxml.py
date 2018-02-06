from symbtr import SymbTrReader


class MusicXMLReader(SymbTrReader):
    def __init__(self):
        """
        Class constructor
        """
        pass

    @classmethod
    def read(cls, score_file, symbtr_name=None):
        """
        Reader method for the SymbTr-MusicXML scores. This method is not
        implemented yet.

        Parameters
        ----------
        score_file : str
            The path of the SymbTr score
        symbtr_name : str, optional
            The name of the score in SymbTr naming convention
            (makam--form--usul--name--composer).
        Returns
        ----------
        NotImplemented
        """
        if symbtr_name is None:
            symbtr_name = MusicXMLReader.get_symbtr_name_from_filepath(
                score_file)

        return NotImplemented
