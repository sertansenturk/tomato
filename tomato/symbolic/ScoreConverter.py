from musicxmlconverter import symbtr2musicxml
from musicxml2lilypond.ScoreConverter import ScoreConverter as XML2LYConverter
from symbtrdataextractor.reader.SymbTrReader import SymbTrReader
from symbtrextras.ScoreExtras import ScoreExtras
from symbtrdataextractor.metadata.MBMetadata import MBMetadata
from ..IO import IO
import os
import subprocess
import tempfile
import re
import musicbrainzngs


class ScoreConverter(object):
    _mb_meta_getter = MBMetadata()
    _xml2ly_converter = XML2LYConverter()

    @classmethod
    def txt_mu2_to_musicxml(cls, symtr_txt_filename, symbtr_mu2_filename,
                            out=None, symbtr_name=None, mbid=None):
        if symbtr_name is None:
            symbtr_name = SymbTrReader.get_symbtr_name_from_filepath(
                symtr_txt_filename)

        mbid_url = cls._get_mbid_url(mbid, symbtr_name)

        piece = symbtr2musicxml.SymbTrScore(
            symtr_txt_filename, symbtr_mu2_filename, symbtrname=symbtr_name,
            mbid_url=mbid_url)

        xmlstr = piece.convertsymbtr2xml()  # outputs the xml score as string
        if out is None:   # return string
            return xmlstr
        else:
            piece.writexml(out)  # save to filename
            return out  # return filename

    @classmethod
    def musicxml_to_lilypond(cls, musicxml_in, lilypond_out=None,
                             render_metadata=True):
        ly_stream, mapping = cls._xml2ly_converter.convert(
            musicxml_in, ly_out=lilypond_out, mapping_out=None,
            render_metadata=render_metadata)

        if lilypond_out is None:
            return ly_stream, mapping
        else:  # ly_stream is already saved to the user-specified file
            return lilypond_out, mapping

    @classmethod
    def lilypond_to_svg(cls, lilypond_in, svg_out=None):
        # create the temporary input to write the lilypond file
        temp_in_file = IO.create_temp_file('.ly', lilypond_in.encode('utf-8'))

        # LilyPond inputs many pages of svg, create a folder for them
        tmp_dir = tempfile.mkdtemp()

        # call lilypond ...
        lilypond_path = cls._get_lilypond_path()
        callstr = u'{0:s} -dpaper-size=\\"junior-legal\\" -dbackend=svg ' \
                  u'-o {1:s} {2:s}'.format(lilypond_path, tmp_dir,
                                           temp_in_file)

        subprocess.call(callstr, shell=True)
        IO.remove_temp_files(temp_in_file)  # remove the temporary .ly input

        # Lilypond saved the svg into pages, i.e. different files with
        # consequent naming.
        svg_files = [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir)]
        svg_files = filter(os.path.isfile, svg_files)
        svg_files = [s for s in svg_files if s.endswith('.svg')]
        svg_files.sort(key=lambda x: os.path.getmtime(x))

        # read the svg files and combine them into one
        regex = re.compile(
            r'.*<a style="(.*)" xlink:href="textedit:///.*'
            r':([0-9]+):([0-9]+):([0-9]+)">.*')
        svg_pages = []
        for f in svg_files:
            svg_file = open(f)
            score = svg_file.read()
            svg_pages.append(regex.sub(
                r'<a style="\1" id="l\2-f\3-t\4" from="\3" to="\4">',
                score))
            svg_file.close()
            os.remove(f)
        os.rmdir(tmp_dir)

        if svg_out is None:  # return string
            # TODO: merge the pages
            return svg_pages
        else:
            with open(svg_out, 'w') as f:
                # TODO: joining the pages produce an invalid svg
                f.write(''.join(svg_pages))
            return svg_out  # output path

    @classmethod
    def _get_mbid_url(cls, mbid, symbtr_name):
        if mbid is None:
            try:
                mbid_url = ScoreExtras.get_mbids(symbtr_name)[0]
            except IndexError:
                mbid_url = None
        else:
            try:  # find if it is a work or recording mbid
                meta = cls._mb_meta_getter.crawl_musicbrainz(mbid)
                mbid_url = meta['url']
            except (musicbrainzngs.NetworkError, musicbrainzngs.ResponseError):
                mbid_url = mbid
        return mbid_url

    @staticmethod
    def _get_lilypond_path():
        return '/home/sertansenturk/bin/lilypond'
        # return "/Applications/LilyPond.app/Contents/Resources/bin/lilypond"
