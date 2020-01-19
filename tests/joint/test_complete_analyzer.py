import os

import pytest


@pytest.mark.smoke
def test_smoke_complete_analyzer():
    from tomato.joint.completeanalyzer import CompleteAnalyzer

    # score input
    symbtr_name = "ussak--sazsemaisi--aksaksemai----neyzen_aziz_dede"
    demo_folder = os.path.join("demos", symbtr_name)
    txt_score_filename = os.path.join(demo_folder, symbtr_name + ".txt")
    mu2_score_filename = os.path.join(demo_folder, symbtr_name + ".mu2")

    # audio input
    audio_mbid = "f970f1e0-0be9-4914-8302-709a0eac088e"
    audio_filename = os.path.join(demo_folder, audio_mbid, audio_mbid + ".mp3")
    complete_analyzer = CompleteAnalyzer()

    complete_features = complete_analyzer.analyze(
        symbtr_txt_filename=txt_score_filename,
        symbtr_mu2_filename=mu2_score_filename,
        symbtr_name=symbtr_name,
        audio_filename=audio_filename,
        audio_metadata=audio_mbid,
    )

    assert complete_features is not None
