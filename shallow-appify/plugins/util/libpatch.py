# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

__author__ = 'Ingo Heimbach'
__email__ = 'i.heimbach@fz-juelich.de'

import logging
import os
import os.path
import re
from .command import exec_cmd


def extract_dependencies(lib_path, dependency_path_prefix):
    dependency_output = exec_cmd('otool -L', lib_path)
    dependencies = []
    for line in dependency_output.split('\n'):
        match_obj = re.match('\s+({prefix}[A-Za-z0-9_/.]+) \('.format(prefix=dependency_path_prefix), line)
        if match_obj:
            current_dependency = match_obj.group(1)
            dependencies.append(current_dependency)
    return dependencies

def replace_install_name(lib_path, new_install_name_prefix):
    lib_name = os.path.basename(lib_path)
    new_install_name = '{new_install_name_prefix}{lib_name}'.format(new_install_name_prefix=new_install_name_prefix,
                                                                    lib_name=lib_name)
    logging.debug('set new install name {name}'.format(name=new_install_name))
    exec_cmd('install_name_tool -id', new_install_name, lib_path)

def replace_dependency(lib_path, old_dependency, new_dependency_prefix):
    old_dependency_lib_name = os.path.basename(old_dependency)
    new_dependency = '{new_dependency_prefix}{lib_name}'.format(new_dependency_prefix=new_dependency_prefix,
                                                                lib_name=old_dependency_lib_name)
    logging.debug('replace dependency {old_dep} with {new_dep}'.format(old_dep=old_dependency, new_dep=new_dependency))
    exec_cmd('install_name_tool -change', old_dependency, new_dependency, lib_path)

def patch_lib(lib_path, old_dependency_prefix, new_dependency_prefix):
    logging.debug('patching library {lib}'.format(lib=lib_path))
    lib_name = os.path.basename(lib_path)
    lib_dependencies = extract_dependencies(lib_path, old_dependency_prefix)
    # replace_install_name(lib_path, new_dependency_prefix) # it is not necessary to change the install name
    for dependency in lib_dependencies:
        replace_dependency(lib_path, dependency, new_dependency_prefix)

def list_libs_from_directory(dir_path):
    return tuple((os.path.join(dir_path, lib) for lib in os.listdir(dir_path) if re.match('.+\.((dylib)|(so))', lib)))

def patch_libs(lib_dir_paths, old_to_new_dependency_prefix_dict):
    for lib_dir_path in lib_dir_paths:
        logging.debug('current library directory: {lib_dir_path}'.format(lib_dir_path=lib_dir_path))
        for lib_path in list_libs_from_directory(lib_dir_path):
            for old_dependency_prefix, new_dependency_prefix in old_to_new_dependency_prefix_dict.iteritems():
                patch_lib(lib_path, old_dependency_prefix, new_dependency_prefix)
