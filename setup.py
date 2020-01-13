import configparser
import os
import subprocess
import zipfile
from io import BytesIO
from urllib.request import urlopen

from setuptools import find_packages, setup
from tomato import __version__

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:  # not necessary, e.g. in Docker
    long_description = ""


class BinarySetup:
    @classmethod
    def setup(cls):
        """Downloads compiled binaries for the OS from the relevant git repos

        Raises:
            OSError: if the OS is not supported.
        """
        bin_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'tomato', 'bin')

        # find os
        sys_os = cls._get_os()

        # read configuration file
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'tomato', 'config', 'bin.cfg')

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(config_file)

        # Download binaries
        for bin_name, bin_url in config.items(sys_os):
            bin_path = os.path.join(bin_folder, bin_name)
            cls._download_binary(bin_path, bin_url, sys_os)

    @staticmethod
    def _get_os():
        process_out = subprocess.check_output(['uname']).lower().decode(
            "utf-8")

        if any(ss in process_out for ss in ['darwin', 'macosx']):
            sys_os = 'macosx'
        elif 'linux' in process_out:
            sys_os = 'linux'
        else:
            raise OSError("Unsupported OS.")

        return sys_os

    @staticmethod
    def _download_binary(fpath, bin_url, sys_os):
        response = urlopen(bin_url)
        if fpath.endswith('.zip'):  # binary in zip
            with zipfile.ZipFile(BytesIO(response.read())) as z:
                z.extractall(os.path.dirname(fpath))
            if sys_os == 'macosx':  # mac executables are in .app
                fpath = os.path.splitext(fpath)[0] + '.app'
            else:  # remove the zip extension
                fpath = os.path.splitext(fpath)[0]
        else:  # binary itself
            with open(fpath, 'wb') as fp:
                fp.write(response.read())

        # make the binary executable
        subprocess.call(["chmod -R +x " + fpath], shell=True)
        print("downloaded %s to %s" % (bin_url, fpath))


# download binaries in advance so they are detected as package data during
# instalation
BinarySetup.setup()


setup(name='tomato',
      version=__version__,
      author='Sertan Senturk',
      author_email='contact AT sertansenturk DOT com',
      maintainer='Sertan Senturk',
      maintainer_email='contact AT sertansenturk DOT com',
      url='https://github.com/sertansenturk/tomato',
      description='Turkish-Ottoman Makam (M)usic Analysis TOolbox',
      long_description=long_description,
      long_description_content_type='text/markdown',
      download_url=(
          'https://github.com/sertansenturk/tomato.git'
          if 'dev' in __version__ else
          'https://github.com/sertansenturk/tomato/releases/tag/'
          'v{0:s}'.format(__version__)),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: GNU Affero General Public License v3 or '
          'later (AGPLv3+)',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Multimedia :: Sound/Audio :: Analysis',
          'Topic :: Scientific/Engineering :: Information Analysis',
          ],
      platforms='Linux',
      license='agpl 3.0',
      keywords=(
          "music-scores analysis tomato audio-recordings lilypond tonic "
          "makam-music score music-information-retrieval "
          "computational-analysis"),
      packages=find_packages(exclude=['docs', 'tests']),
      include_package_data=True,
      python_requires='>=3.5,<3.8',
      install_requires=[
          "numpy>=1.9.0",  # numerical operations
          "scipy>=0.17.0",  # temporary mat file saving for MCR binary inputs
          "pandas>=0.18.0,<=0.24.2",  # tabular data processing
          "matplotlib>=1.5.1,<=3.0.3",  # plotting
          "json_tricks>=3.12.1",  # saving json files with classes and numpy
          "eyeD3>=0.7.5,<=0.8.11",  # reading metadata embedded in recordings
          "python-Levenshtein>=0.12.0",  # semiotic structure labeling
          "networkx>=1.11",  # semiotic structure labeling clique computation
          "lxml>=3.6.0",  # musicxml conversion
          "musicbrainzngs>=0.6",  # metadata crawling from musicbrainz
          "essentia>=2.1b5;platform_system=='Linux'"  # audio signal processing
          ],
      extras_require={
          "development": ["tox", "pylint", "pylint-fail-under", "flake8"],
          "demos": ["jupyter"]
      })
