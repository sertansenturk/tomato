import os
import pytest


@pytest.mark.smoke
def test_smoke_symbtr_converter():
    from tomato.symbolic.symbtrconverter import SymbTrConverter

    # inputs
    symbtr_name = 'ussak--sazsemaisi--aksaksemai----neyzen_aziz_dede'
    score_folder = os.path.join("demos", symbtr_name)
    txt_score_filename = os.path.join(score_folder, symbtr_name + '.txt')
    mu2_score_filename = os.path.join(score_folder, symbtr_name + '.mu2')
    work_mbid = 'e7924b0d-c8a0-4b4a-b253-8eec898eac1e'

    # outputs
    xml_filename = os.path.join(score_folder, symbtr_name + '.xml')
    ly_filename = os.path.join(score_folder, symbtr_name + '.ly')
    svg_filename_template = os.path.join(score_folder, symbtr_name)

    # parameters
    render_metadata = True  # Add the metadata stored in MusicXML to Lilypond
    svg_paper_size = 'junior-legal'  # The paper size of the svg output pages

    symbTrConverter = SymbTrConverter()
    xml_out, ly_out, svg_out, txt_ly_mapping = symbTrConverter.convert(
        txt_score_filename,
        mu2_score_filename,
        symbtr_name=symbtr_name,
        mbid=work_mbid,
        render_metadata=render_metadata,
        xml_out=xml_filename,
        ly_out=ly_filename,
        svg_out=svg_filename_template,
        svg_paper_size=svg_paper_size)
