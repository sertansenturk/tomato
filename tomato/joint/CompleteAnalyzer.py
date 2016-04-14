from ..Analyzer import Analyzer
from ..symbolic.SymbTrAnalyzer import SymbTrAnalyzer
from ..audio.AudioAnalyzer import AudioAnalyzer
from .JointAnalyzer import JointAnalyzer


class CompleteAnalyzer(Analyzer):
    """
    Analyzer class, which does the complete audio analysis, score analysis and
    joint analysis.

    If you need to adjust parameters or if you need a faster, smarter,
    lightweight analysis, you should use the SymbTrAnalyzer, AudioAnalyzer and
    JointAnalyzer classes individually instead.
    """
    _inputs = []

    def __init__(self):
        """
        Initialize a CompleteAnalyzer object
        """
        super(CompleteAnalyzer, self).__init__(verbose=True)

        # extractors
        self._symbtrAnalyzer = SymbTrAnalyzer(verbose=self.verbose)
        self._audioAnalyzer = AudioAnalyzer(verbose=self.verbose)
        self._jointAnalyzer = JointAnalyzer(verbose=self.verbose)

    def analyze(self, symbtr_txt_filename='', symbtr_mu2_filename='',
                symbtr_name=None, audio_filename='', audio_metadata=None):
        """
        Apply complete analysis of the input score(s) and audio recording

        Parameters
        ----------
        symbtr_txt_filename : str
            The SymbTr-score of the performed composition in txt format. It
            is used to parse mainly the notated musical events and with some
            editoral metadata
        symbtr_mu2_filename : str
            The SymbTr-score of the performed composition in mu2 format. It
            is used to parse editorial metadata and music theory
        symbtr_name : str, optional
            The score name in the SymbTr convention, i.e.
            "makam--form--usul--name--composer." If not given the method
            will search the name in the symbtr_txt_filename
        audio_filename : str, optional
            The audio recording of the performed composition
        audio_metadata : str ot bool, optional
            The relevant recording MusicBrainz ID (MBID). IF not given, the
            method will try to fetch the MBID from tags in the recording. If
            the value is False, audio metadata will not be crawled
        Returns
        ----------
        dict
            The summary of the complete analysis from the features computed
            by the best available results.
        dict
            Features computed only using the music scores
        dict
            Features computed only using the audio recordin
        dict
            Features related to audio recording, which are (re-)computed
            after audio-score alignment
        dict
            Features that are related to both the music scores and audio
            recordings.
        """
        # score analysis
        score_features, boundaries, work_mbid = self._symbtrAnalyzer.analyze(
            symbtr_txt_filename, symbtr_mu2_filename, symbtr_name=symbtr_name)

        # audio analysis
        audio_features = self._audioAnalyzer.analyze(
            audio_filename, makam=score_features['makam']['symbtr_slug'],
            metadata=audio_metadata)

        # joint analysis
        joint_features, score_informed_audio_features = self._jointAnalyzer.\
            analyze(symbtr_txt_filename, score_features, audio_filename,
                    audio_features['pitch'])

        # redo some steps in audio analysis
        score_informed_audio_features = self._audioAnalyzer.analyze(
            metadata=False, pitch=False, **score_informed_audio_features)

        # summarize all the features extracted from all sources
        summarized_features = self._jointAnalyzer.summarize(
            audio_features, score_features, joint_features,
            score_informed_audio_features)

        return (summarized_features, score_features, audio_features,
                score_informed_audio_features, joint_features)

    @staticmethod
    def plot(summarized_features):
        return JointAnalyzer.plot(summarized_features)
