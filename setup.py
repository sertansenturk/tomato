#!/usr/bin/env python
import subprocess
from tomato.MCR import MCRSetup

try:
    from setuptools import setup
    from setuptools.command.install import install as _install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install as _install


class CustomInstall(_install):
    def run(self):
        # download the binaries
        self.execute(MCRSetup.setup_binaries(), (),
                     msg="Downloading the binaries from tomato_binaries.")

        # install tomato
        _install.run(self)

        # install requirements
        subprocess.call(["pip install -r requirements"], shell=True)


setup(name='tomato',
      version='0.3',
      author='Sertan Senturk',
      author_email='contact AT sertansenturk DOT com',
      maintainer='Sertan Senturk',
      maintainer_email='contact AT sertansenturk DOT com',
      url='http://sertansenturk.com',
      description='Turkish-Ottoman Makam (M)usic Analysis TOolbox',
      long_description="""\
Turkish-Ottoman Makam (M)usic Analysis TOolbox
----------------------------------------------

tomato is a comprehensive and easy-to-use toolbox for the analysis of audio
recordings and music scores of Turkish-Ottoman makam music.

The aim of the toolbox is to allow the user to easily analyze large-scale
audio recording and music score collections of Turkish-Ottoman makam music,
using the state of the art methodologies specifically designed for the
necessities of this tradition. The analysis results can then be further used
for several tasks such as automatic content description, music
discovery/recommendation and musicological analysis.
      """,
      download_url='https://github.com/sertansenturk/tomato/releases/tag/v0.2',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Information Technology',
          'License :: OSI Approved :: GNU Affero General Public License v3 or '
          'later (AGPLv3+)',
          'Natural Language :: English'
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Sound/Audio :: Analysis',
          'Topic :: Scientific/Engineering :: Information Analysis',
          ],
      platforms='Linux, MacOS X',
      license='agpl 3.0',
      packages=['tomato'],
      include_package_data=True,
      install_requires=[
      ],
      cmdclass={'install': CustomInstall},
      )
