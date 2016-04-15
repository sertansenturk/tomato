from musicxmlconverter.symbtr2musicxml import SymbTrScore
from symbtrdataextractor.reader.SymbTrReader import SymbTrReader
from symbtrextras.ScoreExtras import ScoreExtras
from symbtrdataextractor.metadata.MBMetadata import MBMetadata
import musicbrainzngs


class ScoreConverter(object):
    mb_meta_getter = MBMetadata()
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
                meta = cls.mb_meta_getter.crawl_musicbrainz(mbid)
                mbid_url = meta['url']
            except (musicbrainzngs.NetworkError, musicbrainzngs.ResponseError):
                mbid_url = mbid

        piece = SymbTrScore(symtr_txt_filename, symbtr_mu2_filename,
                            symbtrname=symbtr_name, mbid_url=mbid_url)

        xmlstr = piece.convertsymbtr2xml()  # outputs the xml score as string
        if out is None:
            return xmlstr  # return string
        else:
            piece.writexml(out)  # save to filename
