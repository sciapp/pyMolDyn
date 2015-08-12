# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

__author__ = 'Ingo Heimbach'
__email__ = 'i.heimbach@fz-juelich.de'


import importlib
import pkgutil

_modules = None
_ext2module = None


def _normalize_ext(f):
    def g(file_ext, *args, **kwargs):
        if file_ext.startswith('.'):
            file_ext = file_ext[1:]
        return f(file_ext, *args, **kwargs)
    return g

def _check_ext_availability(f):
    @_normalize_ext
    def g(file_ext, *args, **kwargs):
        if _ext2module is not None:
            if file_ext in _ext2module:
                return f(file_ext, *args, **kwargs)
            else:
                return NotImplemented
        else:
            raise NotInitializedError
    return g

class NotInitializedError(Exception):
    pass


def add_plugin_command_line_arguments(parser):
    for module in _modules.values():
        arguments = module.get_command_line_arguments()
        for name_or_flags, kwargs in arguments:
            if 'help' in kwargs:
                kwargs['help'] = '({plugin_name} only) {help}'.format(plugin_name=module._plugin_name_,
                                                                      help=kwargs['help'])
            if not isinstance(name_or_flags, (tuple, list)):
                name_or_flags = [name_or_flags]
            parser.add_argument(*name_or_flags, **kwargs)

@_check_ext_availability
def parse_command_line_arguments(file_ext, arguments):
    return _ext2module[file_ext].parse_command_line_arguments(arguments)

@_check_ext_availability
def pre_create_app(file_ext, **arguments):
    return _ext2module[file_ext].pre_create_app(**arguments)

@_normalize_ext
def setup_startup(file_ext, app_path, executable_path, app_executable_path,
                  executable_root_path, macos_path, resources_path):
    global _ext2startup_func

    if _ext2module is not None:
        if file_ext in _ext2module:
            return _ext2module[file_ext].setup_startup(app_path, executable_path, app_executable_path,
                                                       executable_root_path, macos_path, resources_path)
        else:
            return NotImplemented
    else:
        raise NotInitializedError

@_check_ext_availability
def post_create_app(file_ext, **arguments):
    return _ext2module[file_ext].post_create_app(**arguments)

def _pkg_init():
    global _modules, _ext2module

    _modules = {}
    _ext2module = {}
    for importer, module_name, is_package in pkgutil.iter_modules(__path__):
        if not is_package:
            current_module = importlib.import_module('.{module_name}'.format(module_name=module_name), 'plugins')
            _modules[module_name] = current_module
            _ext2module[current_module._file_ext_] = current_module


_pkg_init()
