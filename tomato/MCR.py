import ConfigParser
import os
import subprocess
import urllib2
import zipfile
from StringIO import StringIO

from tomato.IO import IO


class MCRCaller(object):
    def __init__(self):
        self.filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'config', 'mcr_path.cfg')
        self.env, self.sys_os = self.set_environment()

    def set_environment(self):
        config = ConfigParser.SafeConfigParser()
        config.read(self.filepath)
        try:
            op_sys, env_var, mcr_path, set_paths = \
                self._get_mcr_config(config, 'custom')
        except (IOError, ValueError):
            try:
                op_sys, env_var, mcr_path, set_paths = \
                    self._get_mcr_config(config, 'linux_default')
            except (IOError, ValueError):
                op_sys, env_var, mcr_path, set_paths = \
                    self._get_mcr_config(config, 'macosx_default')

        subprocess_env = os.environ.copy()
        subprocess_env["MCR_CACHE_ROOT"] = "/tmp/emptydir"
        subprocess_env[env_var] = set_paths

        return subprocess_env, op_sys

    def call(self, callstr):
        proc = subprocess.Popen(callstr, stdout=subprocess.PIPE, shell=True,
                                env=self.env)
        return proc.communicate()

    @classmethod
    def _get_mcr_config(cls, config, section_str):
        op_sys = config.get(section_str, 'sys_os')
        env_var = config.get(section_str, 'env_var')
        mcr_path = config.get(section_str, 'mcr_path')
        set_paths = config.get(section_str, 'set_paths')
        cls._check_mcr_config(env_var, mcr_path)

        return op_sys, env_var, mcr_path, set_paths

    @classmethod
    def _check_mcr_config(cls, env_var, mcr_path):
        if env_var and mcr_path:
            # MCR installation path is not found
            if not os.path.exists(mcr_path):
                raise IOError('The mcr path is not found. Please '
                              'fill the custom section in '
                              '"tomato/config/mcr_path.cfg" manually.')
        elif env_var or mcr_path:  # The configuration is wrong
            raise ValueError('One of the custom fields for the MCR '
                             'path is empty in "tomato/config/mcr_path.cfg". '
                             'Please reconfigure manually.')
        else:
            raise ValueError('Empty fields in the section')

    def get_binary_path(self, bin_name):
        if self.sys_os == 'linux':
            bin_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'bin', bin_name)
        elif self.sys_os == 'macosx':
            bin_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'bin', bin_name + '.app', 'Contents', 'MacOS', bin_name)
        else:
            raise ValueError('Unsupported OS.')

        if not os.path.exists(bin_path):
            raise IOError('Binary does not exist: ' + bin_path)

        return bin_path


class MCRSetup(object):
    @staticmethod
    def setup_binaries():
        """
        Downloads the binaries compiled by MATLAB Runtime Compiler from
        tomato_binaries
        """
        binary_folder = IO.get_abspath_from_relpath_in_tomato('bin')

        operating_system = MCRSetup._get_os()

        # read configuration file
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'tomato', 'config', 'bin.cfg')
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read(config_file)

        # Download binaries
        MCRSetup._download_binaries(binary_folder, config, operating_system)

    @staticmethod
    def _download_binaries(binary_folder, config, sys_os):
        for bin_name, bin_url in config.items(sys_os):
            fpath = os.path.join(binary_folder, bin_name)

            # download
            print("- Downloading binary: " + bin_url)
            response = urllib2.urlopen(bin_url)
            if fpath.endswith('.zip'):  # binary in zip
                with zipfile.ZipFile(StringIO(response.read())) as z:
                    z.extractall(os.path.dirname(fpath))
                if sys_os == 'macosx':  # actual mac executable is in .app
                    fpath = os.path.splitext(fpath)[0] + '.app'
                else:  # remove the zip extension
                    fpath = os.path.splitext(fpath)[0]
            else:  # binary itself
                with open(fpath, 'w+') as fp:
                    fp.write(response.read())

            # make the binary executalbe
            subprocess.call(["chmod -R +x " + fpath], shell=True)

    @staticmethod
    def _get_os():
        # find os, linux or macosx
        process_out = subprocess.check_output(['uname']).lower()
        if any(ss in process_out for ss in ['darwin', 'macosx']):
            sys_os = 'macosx'
        elif 'linux' in process_out:
            sys_os = 'linux'
        else:
            raise OSError("Unsupported OS.")

        return sys_os
