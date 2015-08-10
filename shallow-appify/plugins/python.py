# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

__author__ = 'Ingo Heimbach'
__email__ = 'i.heimbach@fz-juelich.de'

import fnmatch
import itertools
import os
import subprocess
from jinja2 import Template


PY_PRE_STARTUP_CONDA_SETUP = '''
#!/bin/bash
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd ${SCRIPT_DIR}
source ../Resources/conda_env/bin/activate ../Resources/conda_env
python __startup__.py
'''.strip()

PY_STARTUP_SCRIPT = '''
#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import os
import os.path
from xml.etree import ElementTree as ET
from Foundation import NSBundle

def fix_current_working_directory():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

def set_cf_keys():
    bundle = NSBundle.mainBundle()
    bundle_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
    info_plist = ET.parse('../Info.plist')
    root = info_plist.getroot()
    plist_dict = root.find('dict')
    current_key = None
    for child in plist_dict:
        if child.tag == 'key' and child.text.startswith('CF'):  # CoreFoundation key
            current_key = child.text
        elif current_key is not None:
            bundle_info[current_key] = child.text
            current_key = None

def main():
    fix_current_working_directory()
    set_cf_keys()
    import {{ main_module }}
    {{ main_module }}.main()    # a main function is required
if __name__ == '__main__':
    main()
'''.strip()


_plugin_name_ = 'Python'
_file_ext_ = 'py'

_PY_STARTUP_SCRIPT_NAME = '__startup__.py'
_ENV_STARTUP_SCRIPT_NAME = '__startup__.sh'
_CONDA_DEFAULT_PACKAGES = ('pyobjc-framework-cocoa', )
_CONDA_DEFAULT_CHANNELS = ('https://conda.binstar.org/erik', )
_EXT_PYLIB_VARIABLE = 'PYLIBPATH'
_EXT_MAKEFILE_TARGET = 'app_extension_modules'

_create_conda_env = False
_requirements_file = None
_conda_channels = None
_extension_makefile = None


class CondaError(Exception):
    pass

class LibPatchingError(Exception):
    pass

class ExtensionModuleError(Exception):
    pass


def get_command_line_arguments():
    arguments = [(('--conda', ), {'dest': 'conda_req_file', 'action': 'store', 'type': os.path.abspath,
                                  'help': 'Creates a miniconda environment from the given conda requirements file and includes it in the app bundle. Can be used to create self-contained python apps.'}),
                 (('--conda-channels', ), {'dest': 'conda_channels', 'action': 'store', 'nargs': '+',
                                           'help': 'A list of custom conda channels to install packages that are not included in the main anaconda distribution.'}),
                 (('--extension-makefile', ), {'dest': 'extension_makefile', 'action': 'store', 'type': os.path.abspath,
                                               'help': 'Path to a makefile for building python extension modules. The makefile is called with the target "{target}" and a variable "{libvariable}" that holds the path to the conda python library.'.format(target=_EXT_MAKEFILE_TARGET, libvariable=_EXT_PYLIB_VARIABLE)})]
    return arguments

def parse_command_line_arguments(args):
    global _create_conda_env, _requirements_file, _conda_channels, _extension_makefile

    checked_args = {}
    if args.conda_req_file is not None:
        checked_args['python_conda'] = args.conda_req_file
        _requirements_file = args.conda_req_file
        _create_conda_env = True
        if args.conda_channels is not None:
            _conda_channels = args.conda_channels
        if args.extension_makefile is not None:
            _extension_makefile = args.extension_makefile
    return checked_args

def pre_create_app(**kwargs):
    pass

def setup_startup(app_path, executable_path, app_executable_path, executable_root_path, macos_path, resources_path):
    def create_python_startup_script(main_module):
        template = Template(PY_STARTUP_SCRIPT)
        startup_script = template.render(main_module=main_module)
        return startup_script

    def patch_lib_python(env_path):
        env_path = os.path.abspath(env_path)
        python_dir_path = '{env_path}/bin'.format(env_path=env_path)
        lib_pattern = 'libpython*.dylib'
        lib_dir_path = '{env_path}/lib'.format(env_path=env_path)
        python_lib_pathes = tuple(['{lib_dir_path}/{path}'.format(lib_dir_path=lib_dir_path, path=path)
                                   for path in os.listdir(lib_dir_path) if fnmatch.fnmatch(path, lib_pattern)])
        for python_lib_path in python_lib_pathes:
            rel_python_lib_path = '@executable_path/{rel_path}'.format(rel_path=os.path.relpath(python_lib_path, python_dir_path))
            with open(os.devnull, 'w') as dummy:
                try:
                    subprocess.check_call(['install_name_tool', '-id', rel_python_lib_path, python_lib_path],
                                          stdout=dummy, stderr=dummy)
                except subprocess.CalledProcessError:
                    raise LibPatchingError('Could not patch the anaconda python library.')

    def create_conda_env():
        def create_env():
            conda_channels = _conda_channels or []
            with open(os.devnull, 'w') as dummy:
                env_path = '{resources}/{env}'.format(resources=resources_path, env='conda_env')
                try:
                    subprocess.check_call(['conda', 'create', '-p', env_path,
                                           '--file', _requirements_file, '--copy', '--quiet', '--yes']
                                          + list(itertools.chain(*[('-c', channel) for channel in conda_channels])),
                                          stdout=dummy, stderr=dummy)
                    subprocess.check_call(' '.join(['source', '{env_path}/bin/activate'.format(env_path=env_path), env_path, ';',
                                                    'conda', 'install', '--copy', '--quiet', '--yes']
                                                   + list(_CONDA_DEFAULT_PACKAGES)
                                                   + list(itertools.chain(*[('-c', channel) for channel in _CONDA_DEFAULT_CHANNELS]))),
                                          stdout=dummy, stderr=dummy, shell=True)
                except subprocess.CalledProcessError:
                    raise CondaError('The conda environment could not be installed.')
            return env_path

        env_path = create_env()
        patch_lib_python(env_path)

    def build_extension_modules(env_path):
        def get_makefile_path():
            if executable_root_path is not None and \
               _extension_makefile.startswith(os.path.abspath(executable_root_path)):
                makefile_path = '{macos_path}/{rel_makefile_path}'.format(macos_path=macos_path,
                                                                          rel_makefile_path=os.path.relpath(_extension_makefile, executable_root_path))
            else:
                makefile_path = _extension_makefile
            return makefile_path

        env_path = os.path.abspath(env_path)
        lib_dir_path = '{env_path}/lib'.format(env_path=env_path)
        makefile_path = get_makefile_path()
        makefile_dir_path = os.path.dirname(makefile_path)
        with open(os.devnull, 'w') as dummy:
            try:
                subprocess.check_call(['make', '-C', makefile_dir_path,
                                       _EXT_MAKEFILE_TARGET,
                                       '{var}={lib_dir_path}'.format(var=_EXT_PYLIB_VARIABLE, lib_dir_path=lib_dir_path)],
                                      stdout=dummy, stderr=dummy)
            except subprocess.CalledProcessError:
                raise ExtensionModuleError('Extension modules could not be built.')

    main_module = os.path.splitext(app_executable_path)[0].replace('/', '.')
    python_startup_script = create_python_startup_script(main_module)
    with open('{macos}/{startup}'.format(macos=macos_path, startup=_PY_STARTUP_SCRIPT_NAME), 'w') as f:
        f.writelines(python_startup_script.encode('utf-8'))
    if _create_conda_env:
        create_conda_env()
        if _extension_makefile is not None:
            build_extension_modules(env_path='{resources}/{env}'.format(resources=resources_path, env='conda_env'))
        env_startup_script = PY_PRE_STARTUP_CONDA_SETUP
        with open('{macos}/{startup}'.format(macos=macos_path, startup=_ENV_STARTUP_SCRIPT_NAME), 'w') as f:
            f.writelines(env_startup_script.encode('utf-8'))
        new_executable_path = _ENV_STARTUP_SCRIPT_NAME
    else:
        new_executable_path = _PY_STARTUP_SCRIPT_NAME

    return new_executable_path

def post_create_app(**kwargs):
    pass
