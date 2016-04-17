from musicxmlconverter import symbtr2musicxml
from musicxml2lilypond.ScoreConverter import ScoreConverter as XML2LYConverter
from symbtrdataextractor.reader.SymbTrReader import SymbTrReader
from symbtrextras.ScoreExtras import ScoreExtras
from symbtrdataextractor.metadata.MBMetadata import MBMetadata
from ..IO import IO
from six.moves import configparser
from ..BinCaller import BinCaller
import os
import subprocess
import tempfile
import re
import musicbrainzngs

_binCaller = BinCaller()


class ScoreConverter(object):
    _mb_meta_getter = MBMetadata()
    _xml2ly_converter = XML2LYConverter()

    @classmethod
    def convert(cls, symtr_txt_filename, symbtr_mu2_filename, symbtr_name=None,
                mbid=None, render_metadata=True, xml_out=None, ly_out=None,
                svg_out=None):
        xml_output = cls.txt_mu2_to_musicxml(
            symtr_txt_filename, symbtr_mu2_filename, xml_out=xml_out,
            symbtr_name=symbtr_name, mbid=mbid)

        ly_output, ly_mapping = cls.musicxml_to_lilypond(
            xml_in=xml_output, ly_out=ly_out, render_metadata=render_metadata)

        svg_output = cls.lilypond_to_svg(ly_output, svg_out=svg_out)

        # mappings
        note_mappings = {
            'txt_to_xml': '?', 'txt_to_ly': ly_mapping, 'txt_to_svg': '?',
            'xml_to_ly': '?', 'xml_to_svg': '?', 'ly_to_svg': '?'}

        return xml_output, ly_output, svg_output, note_mappings

    @classmethod
    def txt_mu2_to_musicxml(cls, txt_file, mu2_file, xml_out=None,
                            symbtr_name=None, mbid=None):
        if symbtr_name is None:
            symbtr_name = SymbTrReader.get_symbtr_name_from_filepath(
                txt_file)

        mbid_url = cls._get_mbid_url(mbid, symbtr_name)

        piece = symbtr2musicxml.SymbTrScore(
            txt_file, mu2_file, symbtrname=symbtr_name,
            mbid_url=mbid_url)

        xmlstr = piece.convertsymbtr2xml()  # outputs the xml score as string
        if xml_out is None:   # return string
            return xmlstr
        else:
            piece.writexml(xml_out)  # save to filename
            return xml_out  # return filename

    @classmethod
    def musicxml_to_lilypond(cls, xml_in, ly_out=None,
                             render_metadata=True):
        ly_stream, txt2ly_mapping = cls._xml2ly_converter.convert(
            xml_in, ly_out=ly_out, mapping_out=None,
            render_metadata=render_metadata)

        if ly_out is None:
            return ly_stream, txt2ly_mapping
        else:  # ly_stream is already saved to the user-specified file
            return ly_out, txt2ly_mapping

    @classmethod
    def lilypond_to_svg(cls, ly_in, svg_out=None):
        # create the temporary input to write the lilypond file
        temp_in_file = IO.create_temp_file('.ly', ly_in.encode('utf-8'))

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
        config = configparser.SafeConfigParser()
        lily_cfgfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', 'config', 'lilypond.cfg')
        config.read(lily_cfgfile)
        try:  # check custon
            lilypath = config.get('custom', 'custom')
            if not os.path.exists(lilypath):
                raise IOError('The lilypond path is not found. Please '
                              'fill the custom section in '
                              '"tomato/config/lilypond.cfg" manually.')
        except IOError:  # check default from sys_os
            lilypath = config.defaults()[_binCaller.sys_os]

            # linux path is given with $HOME; convert it to the real path
            lilypath = lilypath.replace('$HOME', os.path.expanduser('~'))
            if not os.path.exists(lilypath):
                raise IOError('The lilypond path is not found. Please '
                              'fill the custom section in '
                              '"tomato/config/lilypond.cfg" manually.')

        return lilypath
