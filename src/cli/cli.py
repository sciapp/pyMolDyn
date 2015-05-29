# -*- coding: utf-8 -*-


__all__ = ["CLI"]


import optparse
import os
import thread
import sys
import logging
from datetime import datetime
from core.control import Control
from core.calculation import Calculation, CalculationSettings
from config.configuration import config


shell_colors = {'white_font':     "\033[37m",
                'red_font':       "\033[31m",
                'yellow_font':    "\033[33m",
                'bold_font':      "\033[1m",
                'red_background': "\033[41m",
                'default': "\033[0m"}


get_progress_string = lambda progress: '[' + '='*int(20*progress) + ' '*(20-int(20*progress)) + ']' + ' %.2f' % (100*progress) + ' %'


class FileList(object):
    def __init__(self, global_resolution, global_atom_radius, global_export_dir):
        self.global_resolution = global_resolution
        self.global_atom_radius = global_atom_radius
        self.global_export_dir = global_export_dir
        self.file_list = []

    def append(self, filename, frames=None, resolution=None, atom_radius=None, export_dir=None):
        self.file_list.append((filename, frames, resolution, atom_radius, export_dir))

    def createCalculationSettings(self, default_settings):
        settings_list = []
        for filename, frames, resolution, atom_radius, export_dir in self.file_list:
            if frames is None:
                frames = [-1]
            if resolution is None or self.global_resolution is not None:
                resolution = self.global_resolution
            if atom_radius is None or self.global_atom_radius is not None:
                atom_radius = self.global_atom_radius
            if export_dir is None or self.global_export_dir is not None:
                export_dir = self.global_export_dir
            settings = default_settings.copy()
            # TODO: atom radius
            settings.datasets = {filename: frames}
            settings.resolution = resolution
            settings.exportdir = export_dir
            settings_list.append(settings)
        return settings_list

    def __len__(self):
        return len(self.file_list)

    def __str__(self):
        s = ""
        for filename, frames, resolution, atom_radius, export_dir in self.file_list:
            s += "-> {}".format(filename)
            if frames is not None and frames[0] != -1:
                s += "; frames " + ", ".join([str(f + 1) for f in frames])
            else:
                s += "; all frames"
            if self.global_resolution is not None:
                s += "; resolution {}".format(self.global_resolution)
            elif resolution is not None:
                s += "; resolution {}".format(resolution)
            if self.global_atom_radius is not None:
                s += "; cutoff radius {}".format(self.global_atom_radius)
            elif atom_radius is not None:
                s += "; cutoff radius {}".format(atom_radius)
            s += "\n"
        return s


class Cli(object):
    def __init__(self, control, command_line_params=None):
        if command_line_params is None:
            command_line_params = sys.argv[1:]
            
        self.control = control
        self.options_list = [{"special_type": None,
                              "name": "quiet",
                              "short": "-q",
                              "long": "--quiet",
                              "action": "store_true",
                              "dest": "quiet",
                              "default": False,
                              "type": None,
                              "help": "Less progress information is printed"},
                             {"special_type": "parameter",
                              "name": "atom radius",
                              "short": "-a",
                              "long": "--atomradius",
                              "action": "store",
                              "dest": "atom_radius",
                              "default": None,
                              "type": "float",
                              "help": "cut off radius"},
                             {"special_type": "parameter",
                              "name": "resolution",
                              "short": "-r",
                              "long": "--resolution",
                              "action": "store",
                              "dest": "resolution",
                              "default": None,
                              "type": "int",
                              "help": "vacancy resolution"},
                             {"special_type": "parameter",
                              "name": "output directory",
                              "short": "-o",
                              "long": "--output_directory",
                              "action": "store",
                              "dest": "output_directory",
                              "default": None,
                              "type": "str",
                              "help": "directory to store the results in"},
#                             {"special_type": "parameter",
#                              "name": "bond delta",
#                              "short": "-b",
#                              "long": "--bonddelta",
#                              "action": "store",
#                              "dest": "bond_delta",
#                              "default": None,
#                              "type": "float",
#                              "help": "constant bond delta (when no parameter is given, radii sum criterion (1.15) is used)"},
                             {"special_type": "disable_target",
                              "name": "no alternative cavities",
                              "short": "",
                              "long": "--noalternativecavities",
                              "action": "store_true",
                              "dest": "no_alternative_cavities",
                              "default": False,
                              "type": None,
                              "help": "Alternative (center based) cavities are not calculated."},
                             {"special_type": "disable_target",
                              "name": "no hdf5 export",
                              "short": "",
                              "long": "--nohdf5export",
                              "action": "store_true",
                              "dest": "no_hdf5_export",
                              "default": False,
                              "type": None,
                              "help": "No HDF5 files with results are created"},
                             {"special_type": "disable_target",
                              "name": "no text export",
                              "short": "",
                              "long": "--notextexport",
                              "action": "store_true",
                              "dest": "no_text_export",
                              "default": False,
                              "type": None,
                              "help": "No text files with results are created"}]
        
        (self.options, self.left_args) = self.__parse_options(command_line_params)
        self.previous_progress = None
        self.cancel_callback = lambda : None
        
    
    # -------------------- public methods --------------------
    def start(self):
        
        print sys.argv
        print self.left_args
        file_list = self.__get_file_list(filter(lambda entry: entry[0] != '-', self.left_args))
        
        default_settings = CalculationSettings(dict())
        default_settings.resolution = self.control.config.Computation.std_resolution
        default_settings.domains = True
        default_settings.surface_cavities = True
        default_settings.center_cavities = not self.options.no_alternative_cavities
        default_settings.recalculate = True
        default_settings.exporthdf5 = not self.options.no_hdf5_export
        default_settings.exporttext = not self.options.no_text_export
        default_settings.exportdir = None
        default_settings.bonds = True
        default_settings.dihedral_angles = True
        settings_list = file_list.createCalculationSettings(default_settings)
        if self.options.atom_radius is not None:
            config.Computation.atom_radius = self.options.atom_radius

        print 'processing files:'
        print file_list
        print 'parameters:'
        tmp_param_string=""
        for i, opt_dict in enumerate(self.options_list):
            tmp_param_string += opt_dict['name'] + ': ' + str(getattr(self.options, opt_dict['dest'])) + ', ' + ('\n' if i % 4 == 3 else '') 
        if tmp_param_string[-1] == '\n':
            tmp_param_string = tmp_param_string[:-3]
        else: 
            tmp_param_string = tmp_param_string[:-2]
        print tmp_param_string
        print
        print '='*80

        if len(settings_list) > 0:
            print "Started calculation: {}".format(datetime.now())
            started_computation = False
            for settings in settings_list:
                print "Calculating File:",
                for filename, _ in settings.datasets.iteritems():
                    print filename,
                print "...",
                sys.stdout.flush()
                results = self.control.calculation.calculate(settings)
                print "Done."
            print "Finished calculation: {}".format(datetime.now())

            #    started_computation = True
        
            #if started_computation:
            #    #self.__handle_input()
            #    try:
            #        self.control.request_action(Actions.Computation.WAIT_UNTIL_FINISHED, [True])
            #    except KeyboardInterrupt:
            #        try:
            #            self.cancel_callback()
            #        except task.IllegalTaskStateException:
            #            pass
                
    
    # -------------------- private methods -------------------
    
    def __handle_input(self):
        while True:
            try:
                line = raw_input()
            except EOFError:
                self.cancel_callback()
                break
            except KeyboardInterrupt:
                self.cancel_callback()
                break
            except ValueError:         # Wird beim Schliessen von stdin geworfen
                self.cancel_callback()
                break
        print
    
    def __parse_options(self, command_line_params):
        usage = """Usage: %prog [options] batch_file1 batch_file2 ...

Batch files have the format:

RESOLUTION resolution
ATOM_RADIUS radius
OUTPUT_DIRECTORY directory
file-01.xyz
file-02.xyz frame frame ...
    .
    .
    .

RESOLUTION, ATOM_RADIUS and OUTPUT_DIRECTORY are optional and are overridden by the command line options. OUTPUT_DIRECTORY can contain one or more asterisks. These are replaced with the subdirectory name(s) containing the input files.
Note: Because the cutoff radius is stored in the global configuration, it cannot yet be specified per calculation. Therefore the ATOM_RADIUS can only be specified on the command line."""
        parser = optparse.OptionParser(usage=usage)
        
        for opt_dict in self.options_list:
            parser.add_option(opt_dict["short"],
                              opt_dict["long"],
                              action=opt_dict["action"],
                              dest=opt_dict["dest"],
                              default=opt_dict["default"], 
                              type=opt_dict["type"],
                              help=opt_dict["help"])
        
        (options, left_args) = parser.parse_args(command_line_params)
        if len(left_args) == 0:
            parser.print_help()
            sys.exit()
        return (options, left_args)
    
    def __get_file_list(self, input_file_list):
        result_file_list = FileList(self.options.resolution,
                                    self.options.atom_radius,
                                    self.options.output_directory)
        for input_file in input_file_list:
            try:
                with open(input_file) as f:
                    resolution = None
                    atom_radius = None
                    output_directory = None
                    for line in f.readlines():
                        lstripped_line = line.lstrip()
                        if len(lstripped_line) > 0 and lstripped_line[0] != '#':
                            line_parts = lstripped_line.split()
                            if line_parts[0] == "RESOLUTION":
                                resolution = int(line_parts[1])
                                continue
                            if line_parts[0] == "ATOM_RADIUS":
                                atom_radius = float(line_parts[1])
                                continue
                            if line_parts[0] == "OUTPUT_DIRECTORY":
                                output_directory = " ".join(line_parts[1:])
                                continue

                            filepath = os.path.join(os.path.dirname(os.path.abspath(input_file)), line_parts[0])
                            if len(line_parts) > 1:
                                frames = [int(f) - 1 for f in line_parts[1:]]
                            else:
                                frames = None
                            result_file_list.append(filepath, frames, resolution, atom_radius, output_directory)
            except IOError:
                print 'warning: batch file %s not accessable and skipped' % (os.path.abspath(input_file))
                        
        return result_file_list

