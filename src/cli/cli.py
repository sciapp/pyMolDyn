import optparse
import os
import thread
import sys
import logging
from core.control import Control
from core.calculation import Calculation, CalculationSettings


shell_colors = {'white_font':     "\033[37m",
                'red_font':       "\033[31m",
                'yellow_font':    "\033[33m",
                'bold_font':      "\033[1m",
                'red_background': "\033[41m",
                'default': "\033[0m"}

get_progress_string = lambda progress: '[' + '='*int(20*progress) + ' '*(20-int(20*progress)) + ']' + ' %.2f' % (100*progress) + ' %'

class Cli(object):
    def __init__(self, controller, command_line_params=None):
        if command_line_params is None:
            command_line_params = sys.argv[1:]
            
        self.controller = controller
        self.options_list = [{"special_type": None,
                              "name": "quiet",
                              "short": "-q",
                              "long": "--quiet",
                              "action": "store_true",
                              "attribute": None,
                              "target": None,
                              "dest": "quiet",
                              "default": False,
                              "type": None,
                              "help": "Less progress information is printed"},
                             {"special_type": "parameter",
                              "name": "atom radius",
                              "short": "-a",
                              "long": "--atomradius",
                              "action": "store",
                              "attribute": Attributes.Settings.ATOM_RADIUS,
                              "target": None,
                              "dest": "atom_radius",
                              "default": self.controller.request_action(Actions.Settings.GET_ATOM_RADIUS, [True]),
                              "type": "float",
                              "help": "cut off radius"},
                             {"special_type": "parameter",
                              "name": "domain resolution",
                              "short": "-d",
                              "long": "--domainresolution",
                              "action": "store",
                              "attribute": Attributes.Settings.VACANCY_RESOLUTION,
                              "target": None,
                              "dest": "domain_resolution",
                              "default": self.controller.request_action(Actions.Settings.GET_VACANCY_RESOLUTION, [True]),
                              "type": "int",
                              "help": "vacancy domain resolution"},
                             {"special_type": "parameter",
                              "name": "alternative cavity resolution",
                              "short": "-c",
                              "long": "--altcavityresolution",
                              "action": "store",
                              "attribute": Attributes.Settings.ALT_CAVITY_RESOLUTION,
                              "target": None,
                              "dest": "alt_cavity_resolution",
                              "default": self.controller.request_action(Actions.Settings.GET_ALT_CAVITY_RESOLUTION, [True]),
                              "type": "int",
                              "help": "alternative cavity resolution"},
                             {"special_type": "parameter",
                              "name": "bond delta",
                              "short": "-b",
                              "long": "--bonddelta",
                              "action": "store",
                              "attribute": Attributes.Settings.BOND_DELTA,
                              "target": None,
                              "dest": "bond_delta",
                              "default": None,
                              "type": "float",
                              "help": "constant bond delta (when no parameter is given, radii sum criterion (1.15) is used)"},
                             {"special_type": "disable_target",
                              "name": "no domains",
                              "short": "",
                              "long": "--nodomains",
                              "action": "store_true",
                              "attribute": None,
                              "target": Targets.VACANCY_MESH_TRANSFORMATION,
                              "dest": "no_domains",
                              "default": False,
                              "type": None,
                              "help": "No domain calculation is done. When cavity calculation is selected only needed domain information is computed."},
                             {"special_type": "disable_target",
                              "name": "no analytic cavities",
                              "short": "",
                              "long": "--noanalyticcavities",
                              "action": "store_true",
                              "attribute": None,
                              "target": Targets.CAVITY_MESH_TRANSFORMATION,
                              "dest": "no_analytic_cavities",
                              "default": False,
                              "type": None,
                              "help": "Analytic cavities are not computed."},
                             {"special_type": "disable_target",
                              "name": "no alternative cavities",
                              "short": "",
                              "long": "--noalternativecavities",
                              "action": "store_true",
                              "attribute": None,
                              "target": Targets.ALT_CAVITY_MESH_TRANSFORMATION,
                              "dest": "no_alternative_cavities",
                              "default": False,
                              "type": None,
                              "help": "Alternative cavities are not calculated."},
                             {"special_type": "disable_target",
                              "name": "no bond information",
                              "short": "",
                              "long": "--nobondinfo",
                              "action": "store_true",
                              "attribute": None,
                              "target": Targets.BOND_INFO,
                              "dest": "no_bond_info",
                              "default": False,
                              "type": None,
                              "help": "No pieces of bond information are calculated."},
                             {"special_type": "extra_option",
                              "name": "export of vacancy central points",
                              "short": "-e",
                              "long": "--exportcentralpoints",
                              "action": "store",
                              "attribute": None,
                              "target": None,
                              "dest": "export_central_points",
                              "default": None,
                              "type": "string",
                              "help": "Export calculated vacancy central points to the given path."},
                             {"special_type": "extra_option",
                              "name": "export of dihedral angles",
                              "short": "-n",
                              "long": "--exportdihedralangles",
                              "action": "store",
                              "attribute": None,
                              "target": None,
                              "dest": "export_dihedral_angles",
                              "default": None,
                              "type": "string",
                              "help": "Export dihedral angles to the given path."}]
        
        (self.options, self.left_args) = self.__parse_options(command_line_params)
        self.previous_progress = None
        self.cancel_callback = lambda : None
        
    
    # -------------------- public methods --------------------
    def start(self):
        
        file_list = self.__get_file_list(filter(lambda entry: entry[0] != '-', self.left_args))
        
        if len(file_list) > 0:
            print _('processing files:')
            for file_dict in file_list:
                try:
                    print _('-> %s (%d frames)' % (file_dict['name'], self.controller.request_action(Actions.Data.GET_BLOCK_COUNT, [file_dict['name']])))
                except FileNotFoundException:
                    pass
            print _('parameters:')
            
            tmp_param_string=""
            for i, opt_dict in enumerate(self.options_list):
                tmp_param_string += opt_dict['name'] + ': ' + str(getattr(self.options, opt_dict['dest'])) + ', ' + ('\n' if i % 4 == 3 else '') 
            if tmp_param_string[-1] == '\n':
                tmp_param_string = tmp_param_string[:-3]
            else: 
                tmp_param_string = tmp_param_string[:-2]
            
            print tmp_param_string
            print
            print '='*100
            
            for opt_dict in self.options_list:
                if opt_dict['special_type'] == 'parameter':
                    self.controller.request_action(Attributes.get_action_setter_id(opt_dict['attribute']), [getattr(self.options, opt_dict['dest'])])   
            
            target_list = []
            for opt_dict in self.options_list:
                if opt_dict['special_type'] == "disable_target":
                    if not getattr(self.options, opt_dict['dest']):
                        target_list.append(opt_dict['target'])
            
            started_computation = False
            for file_dict in file_list:
                try:
                    self.controller.request_action(Actions.Data.OPEN_NEW_FILE, [file_dict['name']], [self])
                    self.controller.request_action(Actions.Settings.SET_BOX_SIZE, [file_dict['box_size']])
                    for block in range(self.controller.request_action(Actions.Data.GET_BLOCK_COUNT, [file_dict['name']])):
                        self.controller.request_action(Actions.Data.PROCESS_DATA, [target_list, [], file_dict['name'], block])
                        started_computation = True
                except FileNotFoundException:
                    pass
        
            if started_computation:
                #self.__handle_input()
                try:
                    self.controller.request_action(Actions.Computation.WAIT_UNTIL_FINISHED, [True])
                except KeyboardInterrupt:
                    try:
                        self.cancel_callback()
                    except task.IllegalTaskStateException:
                        pass
                
    
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
        parser = optparse.OptionParser(usage=_("Usage: %s [options] batch_file1 batch_file2 ...\n\nBatch files have the format:\n\nxyz-file-01\tbox-size (in angstrom units)\nxyz-file-02\tbox-size\n   .\n   .\n   .") % '%prog')
        
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
        file_dict_keys = ['name', 'box_size']
        key_types = {'name': str, 'box_size': float}
        
        result_file_list = []
        
        for input_file in input_file_list:
            try:
                with open(input_file) as f:
                    for line in f.readlines():
                        lstripped_line = line.lstrip()
                        if len(lstripped_line) > 0 and lstripped_line[0] != '#':
                            line_parts = []
                            for i, part in enumerate(line.split()):
                                if file_dict_keys[i] == 'name':
                                    line_parts.append(os.path.dirname(os.path.abspath(input_file)) + '/' + part)
                                else:
                                    line_parts.append(key_types[file_dict_keys[i]](part))
                            result_file_list.append(dict(zip(file_dict_keys, line_parts)))
            except IOError:
                print _('warning: batch file %s not accessable and skipped') % (os.path.abspath(input_file))
                        
        return result_file_list
    
    def __delete_progress(self, progress, progress_func):
        if progress is not None:
            char_count = len(progress_func(progress))
            sys.stdout.write('\b' * char_count)
            sys.stdout.write(' ' * char_count)
            sys.stdout.write('\b' * char_count)
            
    def __finished_targets(self, status, filename, block, mds_save, finished_job_queue):
        # Wenn kein Fehler oder Abbruch aufgetreten ist....
        if status == task.FINISHED:
            def write_export_file(info_text, path, suffix, action, ext=None):
                sys.stdout.write('\n-> %s ' % _(info_text))
                (base, file_ext) = os.path.splitext(os.path.basename(filename))
                if ext is None:
                    ext = file_ext
                name = path + (os.sep if path[-1] != os.sep else '') + base + suffix + ext
                result = self.controller.request_action(action, [name, True, 'w' if block == 0 else 'a'] if action == Actions.Data.WRITE_VACANCY_CENTRAL_POINTS_AS_XYZ else [name, 'w' if block == 0 else 'a'])
                sys.stdout.write(('%s' % _('done')) if result else ('%s' % _('failed')))

            if not self.options.no_domains and self.options.export_central_points is not None:
                write_export_file('export cavity central points...', self.options.export_central_points, '_with_cavity_central_points', Actions.Data.WRITE_VACANCY_CENTRAL_POINTS_AS_XYZ)
            if not self.options.no_bond_info and self.options.export_dihedral_angles is not None:
                write_export_file('export dihedral angles...', self.options.export_dihedral_angles, '_dihedral_angles', Actions.Data.WRITE_DIHEDRAL_ANGLES, '.ang')

        self.cancel_callback = lambda : None
        print
        print
        if finished_job_queue:
            pass
            # sys.stdin.close()                 # Zwinge Einlesethread zum Beenden der Einleseroutine
    
    # -------------------- interface methods -----------------
    
    def set_attribute(self, attribute, parameter_list):
        
        if attribute == Attributes.Computation.STARTED_COMPUTATION:
            print '\n-> %s' % (_('file: %s, frame: %d') % (str(parameter_list[0]), parameter_list[1]))
            print '   %s' % (_('current box size: %f') % (self.controller.request_action(Actions.Settings.GET_BOX_SIZE)))
        elif attribute == Attributes.Computation.STATUS or attribute == Attributes.Recording.STATUS:
            if not self.options.quiet:
                self.__delete_progress(self.previous_progress, get_progress_string)
                self.previous_progress = None
                sys.stdout.write('\n---> ' + parameter_list[0] + ' ')
                sys.stdout.flush()
        elif attribute == Attributes.Computation.PROGRESS or attribute == Attributes.Recording.PROGRESS:
            if not self.options.quiet:
                self.__delete_progress(self.previous_progress, get_progress_string)
                if parameter_list[0] is not None:    
                    sys.stdout.write(get_progress_string(parameter_list[0]))
                    sys.stdout.flush()
                self.previous_progress = parameter_list[0]
        elif attribute == Attributes.Computation.FINISHED_TARGETS:
            self.__finished_targets(*parameter_list)
        elif attribute == Attributes.Computation.CANCEL_CALLBACK:
            self.cancel_callback = parameter_list[0]
        elif attribute == Attributes.Consistency.WRITABLE_MDS_DIR or attribute == Attributes.Consistency.ACCESSIBLE_MDS_DIR:
            if not parameter_list[0]:
                sys.stderr.write('%spyMoldyn will quit because computations cannot be performed.%s\n\n' % (('%s%s') % (shell_colors['red_font'], shell_colors['bold_font']), shell_colors['default']))
                sys.exit(1)
                
        elif attribute == Attributes.Settings.LOGGING_ENABLED:
            if parameter_list[0]:
                logging.disable(logging.NOTSET)
            else:
                logging.disable(logging.INFO)
        elif attribute == Attributes.Error.ERRORLOG:
            do_shutdown = parameter_list[-1]
            sys.stderr.write("\n\n")
            for error in parameter_list[:-1]:
                (title, static, dyn) = error
                sys.stderr.write('%s%s%s\n' %('%s%s' % (shell_colors['red_font'], shell_colors['bold_font']), title, shell_colors['default']))
                sys.stderr.write('%s%s%s\n' %('%s' % (shell_colors['red_font']), static, shell_colors['default']))
                for t in dyn:
                    sys.stderr.write(' - %s%s%s\n' %('%s' % (shell_colors['red_font']), t, shell_colors['default']))
                sys.stderr.write('\n')
            if do_shutdown:
                thread.interrupt_main()
