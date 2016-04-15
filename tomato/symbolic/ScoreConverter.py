from musicxmlconverter import symbtr2musicxml
from musicxml2lilypond import musicxml2lilypond
from symbtrdataextractor.reader.SymbTrReader import SymbTrReader
from symbtrextras.ScoreExtras import ScoreExtras
from symbtrdataextractor.metadata.MBMetadata import MBMetadata

import musicbrainzngs


class ScoreConverter(object):
    _mb_meta_getter = MBMetadata()
    _xml2ly_converter = musicxml2lilypond.ScoreConverter()

    @classmethod
    def txt_mu2_to_musicxml(cls, symtr_txt_filename, symbtr_mu2_filename,
                            out=None, symbtr_name=None, mbid=None):
        if symbtr_name is None:
            symbtr_name = SymbTrReader.get_symbtr_name_from_filepath(
                symtr_txt_filename)

        if mbid is None:
            mbid_url = ScoreExtras.get_mbids(symbtr_name)[0]
        else:
            try:
                meta = cls._mb_meta_getter.crawl_musicbrainz(mbid)
                mbid_url = meta['url']
            except (musicbrainzngs.NetworkError, musicbrainzngs.ResponseError):
                mbid_url = mbid

        piece = symbtr2musicxml.SymbTrScore(
            symtr_txt_filename, symbtr_mu2_filename, symbtrname=symbtr_name,
            mbid_url=mbid_url)

        xmlstr = piece.convertsymbtr2xml()  # outputs the xml score as string
        if out is None:
            return xmlstr  # return string
        else:
            piece.writexml(out)  # save to filename

    @classmethod
    def musicxml_to_lilypond(cls, symtr_xml_in, lilypond_out=None,
                             render_metadata=False):
        ly_stream, mapping = cls._xml2ly_converter.run(
            symtr_xml_in, ly_out=lilypond_out, map_out=None,
            render_metadata=render_metadata)

        if lilypond_out is None:
            return mapping, ly_stream
        else:  # ly_stream is already saved to the user-specified file
            return mapping
