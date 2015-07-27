#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

__author__ = 'Ingo Heimbach'
__email__ = 'i.heimbach@fz-juelich.de'

__version_info__ = (0, 1, 1)
__version__ = '.'.join(map(str, __version_info__))

import argparse
import os
import os.path
import re
import shutil
import subprocess
import sys
import tempfile
from jinja2 import Template
from PIL import Image
import logging
logging.basicConfig(level=logging.WARNING)


INFO_PLIST_TEMPLATE = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    {% if environment -%}
    <key>LSEnvironment</key>
    <dict>
        {% for key, value in environment.iteritems() -%}
        <key>{{ key }}</key>
        <string>{{ value }}</string>
        {% endfor -%}
    </dict>
    {% endif -%}
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>{{ executable }}</string>
    {% if icon_file -%}
    <key>CFBundleIconFile</key>
    <string>{{ icon_file }}</string>
    {% endif -%}
    <key>CFBundleIdentifier</key>
    <string>undefined.{{ name }}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{{ name }}</string>
    <key>CFBundleDisplayName</key>
    <string>{{ name }}</string>
    <key>CFBundleShortVersionString</key>
    <string>{{ short_version }}</string>
    <key>CFBundleVersion</key>
    <string>{{ version }}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
</dict>
</plist>
'''.strip()

PKG_INFO_CONTENT = 'APPL????'

STARTUP_SKRIPT = '''
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




class TemporaryDirectory(object):
    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp()

    def __enter__(self):
        return self.tmp_dir

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.tmp_dir)
        self.tmp_dir = None


class Arguments(object):
    def __init__(self, **kwargs):
        super(Arguments, self).__setattr__('_members', {})
        for key, value in kwargs.iteritems():
            self._members[key] = value

    def __getattr__(self, attr):
        return self._members[attr]

    def __setattr__(self, key, value):
        raise NotImplementedError

    def __getitem__(self, item):
        return getattr(self, item)

    def keys(self):
        return self._members.keys()


class MissingIconError(Exception):
    pass

class AppAlreadyExistingError(Exception):
    pass

class InvalidAppPath(Exception):
    pass


def parse_args():
    def parse_commandline():
        parser = argparse.ArgumentParser(description='''
        Creates a runnable application for Mac OS X with references to
        system libraries. The result is a NON-self-contained app bundle.''')
        parser.add_argument('-d', '--executable-directory', dest='executable_root_path', action='store', type=os.path.abspath,
                            help='Defines the executable root directory that will be included in the app.')
        parser.add_argument('-i', '--icon', dest='icon_path', action='store', type=os.path.abspath,
                            help='Image file that is used for app icon creation. It must be quadratic with a resolution of 1024x1024 pixels or more.')
        parser.add_argument('-e', '--environment', dest='environment_vars', action='store', nargs='+',
                            help='Specifies which environment variables -- set on the current interpreter startup -- shall be included in the app bundle.')
        parser.add_argument('-o', '--output', dest='app_path', action='store', type=os.path.abspath,
                            help='Sets the path the app will be saved to.')
        parser.add_argument('-v', '--version', dest='version_string', action='store',
                            help='Specifies the version string of the program.')
        parser.add_argument('executable_path', action='store', type=os.path.abspath,
                            help='Sets the executable that is started when the app is opened.')
        if len(sys.argv) < 2:
            parser.print_help()
            sys.exit(1)
        args = parser.parse_args()
        return args

    def map_environment_arguments_to_dict(enviroment_argument_list):
        if enviroment_argument_list is not None:
            keys_and_values = [item.split('=') for item in enviroment_argument_list]
            for item in keys_and_values:
                if len(item) < 2:
                    item.append(os.environ[item[0]])
            result = dict(keys_and_values)
        else:
            result = None
        return result

    args = parse_commandline()
    executable_root_path = args.executable_root_path
    icon_path = args.icon_path
    environment_vars = map_environment_arguments_to_dict(args.environment_vars)
    if args.app_path is not None:
        app_path = args.app_path
    else:
        app_path = '{basename_without_ext}.app'.format(basename_without_ext=os.path.splitext(os.path.basename(os.path.abspath(args.executable_path)))[0])
    if args.version_string is not None:
        version_string = args.version_string
    else:
        version_string = '0.0.0'
    executable_path = args.executable_path

    return Arguments(executable_root_path=executable_root_path,
                     icon_path=icon_path,
                     environment_vars=environment_vars,
                     app_path=app_path,
                     version_string=version_string,
                     executable_path=executable_path)

def create_info_plist_content(app_name, version, executable_path, executable_root_path=None, icon_path=None, environment_vars=None):
    def get_short_version(version):
        match_obj = re.search('\d+(\.\d+){0,2}', version)
        if match_obj is not None:
            short_version = match_obj.group()
            while not re.match('\d+\.\d+\.\d+', short_version):
                short_version += '.0'
        else:
            short_version = '0.0.0'
        return short_version

    if executable_root_path is None:
        executable_root_path = os.path.dirname(executable_path)

    if os.path.abspath(executable_path).startswith(os.path.abspath(executable_root_path)):
        executable = os.path.relpath(executable_path, executable_root_path)
    else:
        executable = executable_path

    vars = {'executable': executable,
            'icon_file': os.path.basename(icon_path) if icon_path is not None else None,
            'name': app_name,
            'short_version': get_short_version(version),
            'version': version}

    if environment_vars is not None:
        environment_variables = dict(((key, os.environ[key]) for key in environment_vars))
        vars['environment'] = environment_variables

    template = Template(INFO_PLIST_TEMPLATE)
    info_plist = template.render(**vars)

    return info_plist

def create_python_startup_script(main_module_name):
    template = Template(STARTUP_SKRIPT)
    startup_script = template.render(main_module=main_module_name)

    return startup_script

def create_icon_set(icon_path, iconset_out_path):
    with TemporaryDirectory() as tmp_dir:
        tmp_icns_dir = '{tmp_dir}/icon.iconset'.format(tmp_dir=tmp_dir)
        os.mkdir(tmp_icns_dir)
        original_icon = Image.open(icon_path)
        for name, size in (('icon_{size}x{size}{suffix}.png'.format(size=size, suffix=suffix), factor*size)
                                for size in (16, 32, 128, 256, 512)
                                    for factor, suffix in ((1, ''), (2, '@2x'))):
            resized_icon = original_icon.resize((size, size), Image.ANTIALIAS)
            resized_icon.save('{icns_dir}/{icon_name}'.format(icns_dir=tmp_icns_dir, icon_name=name))
        subprocess.call(('iconutil', '--convert', 'icns', tmp_icns_dir, '--output', iconset_out_path))

def create_app(app_path, version_string, executable_path, executable_root_path=None, icon_path=None, environment_vars=None):
    def abs_path(relative_bundle_path, base=None):
        return os.path.abspath('{app_path}/{dir}'.format(app_path=app_path if base is None else base, dir=relative_bundle_path))

    def error_checks():
        if os.path.exists(abs_path('.')):
            raise AppAlreadyExistingError('The app path {app_path} already exists.'.format(app_path=app_path))
        if abs_path('.').startswith(os.path.abspath(executable_root_path)):
            raise InvalidAppPath('The specified app path is a subpath of the source root directory.')

    def write_info_plist():
        info_plist_content = create_info_plist_content(app_name, version_string, app_executable_path, executable_root_path,
                                                       bundle_icon_path, environment_vars)
        with open(abs_path('Info.plist', contents_path) , 'w') as f:
            f.writelines(info_plist_content.encode('utf-8'))

    def write_pkg_info():
        with open(abs_path('PkgInfo', contents_path) , 'w') as f:
            f.write(PKG_INFO_CONTENT)

    def copy_source():
        if executable_root_path is None:
            shutil.copy(executable_path, macos_path)
        else:
            os.rmdir(macos_path)
            shutil.copytree(executable_root_path, macos_path)

    def set_file_permissions():
        os.chmod(abs_path(app_executable_path, macos_path), 0555)

    class StartupSetup(object):
        '''
        Class that contains functions to handle the startup of specific program types, e.g. python scripts.
        Extend with more methods to support further languages if necessary. To do so, add a static method
        named '_<program-file-extension>_startup' and create an own startup script. The variable
        'app_executable_path' contains the relative path in the app bundle to the original executable file.
        The method must return the path to newly created startup script.
        See '_py_startup' as an example.
        '''
        @staticmethod
        def _py_startup():
            main_module = os.path.splitext(app_executable_path)[0].replace('/', '.')
            python_startup_script = create_python_startup_script(main_module)
            new_executable_path = '___startup___.py'
            with open(abs_path(new_executable_path, macos_path), 'w') as f:
                f.writelines(python_startup_script.encode('utf-8'))
            return new_executable_path

        @classmethod
        def setup_startup(cls, file_ext):
            if file_ext.startswith('.'):
                file_ext = file_ext[1:]
            if not hasattr(cls, '_ext2func'):
                cls._ext2func = {}
                for key, value in cls.__dict__.iteritems():
                    match = re.search('_[a-z]+_startup', key)
                    if match:
                        cls._ext2func[match.group()[1:-len('_startup')]] = value
            if file_ext in cls._ext2func:
                return cls._ext2func[file_ext].__func__()
            else:
                return NotImplemented


    directory_structure = ('Contents', 'Contents/MacOS', 'Contents/Resources')
    contents_path, macos_path, resources_path = (abs_path(dir) for dir in directory_structure)
    bundle_icon_path = abs_path('Icon.icns', resources_path) if icon_path is not None else None
    app_name = os.path.splitext(os.path.basename(app_path))[0]
    if executable_root_path is not None:
        app_executable_path = os.path.relpath(executable_path, executable_root_path)
    else:
        app_executable_path = os.path.basename(executable_path)

    error_checks()

    for current_path in (abs_path(dir) for dir in directory_structure):
        os.makedirs(current_path)
    copy_source()
    if icon_path is not None:
        try:
            create_icon_set(icon_path, bundle_icon_path)
        except IOError as e:
            raise MissingIconError(e)
    setup_result = StartupSetup.setup_startup(os.path.splitext(app_executable_path)[1])
    if setup_result is not NotImplemented:
        app_executable_path = setup_result
    write_info_plist()
    write_pkg_info()
    set_file_permissions()

def main():
    args = parse_args()
    try:
        create_app(**args)
    except Exception as e:
        sys.stderr.write('Error: {message}\n'.format(message=e))


if __name__ == '__main__':
    main()
