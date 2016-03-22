#!/usr/bin/env python
import os, sys
try:
    from setuptools import setup
    from setuptools.command.install import install as _install
except ImportError:
    from distutils.core import setup
    from distutils.command.install import install as _install


def _get_mcr_binaries():
    """
    Downloads the binaries compiled by MATLAB Runtime Compiler from tomato_binaries
    """
    import subprocess
    import ConfigParser
    import urllib

    binary_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tomato', '_binaries')

    # find os, linux or macosx
    process_out = subprocess.check_output(['uname']).lower()
    if any(ss in process_out for ss in ['darwin', 'macosx']):
        sys_os = 'MacOSX'
    elif 'linux' in process_out:
        sys_os = 'Linux'
    else:
        raise OSError("Unsupported OS.")

    # read configuration file
    config_file = os.path.join('config', 'binaries.cfg')
    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(config_file)

    # Download binaries
    for bin_pair in config.items(sys_os):
        fpath = os.path.join(binary_folder, bin_pair[0])
        print("- Downloading binary: " + bin_pair[0])
        urllib.urlretrieve(bin_pair[1], fpath)


class CustomInstall(_install):
    def run(self):
        _install.run(self)
        self.execute(_get_mcr_binaries, (),
                     msg="Downloading the binaries from tomato_binaries.")

setup(name='tomato',
      version='0.1',
      author='Sertan Senturk',
      author_email='contact AT sertansenturk DOT com',
      license='agpl 3.0',
      description='Turkish-Ottoman Makam Music Analysis Toolbox',
      url='http://sertansenturk.com',
      packages=['tomato'],
      include_package_data=True,
      install_requires=[
          "numpy",
          "matplotlib"
      ],
      cmdclass={'install': CustomInstall},
      )
