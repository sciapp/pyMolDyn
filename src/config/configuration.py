import configobj
import validate
import os.path
import inspect

CONFIG_FILE = 'config/config.cfg'
CONFIG_SPEC_FILE = 'config/config.spec'

# second string is the list type name
type_dict = {
    int: ('integer', 'int'),
    float: ('float', 'float'),
    str: ('string', 'string'),
    bool: ('boolean', 'bool'),
}


class ConfigNode:

    def __init__(self):
        pass


class Configuration(ConfigNode):
    """
    Configuration Object that contains the application settings
    """

    class Colors(ConfigNode):

        def __init__(self):
            self.cavity         = [0.2, 0.4, 1.]
            self.domain         = [0., 1., 0.5]
            self.alt_cavity     = [0.9, 0.4, 0.2]
            self.background     = [0.0, 0.0, 0.0]
            self.bounding_box   = [1.0, 1.0, 1.0]
            self.atoms          = [1.0, 1.0, 1.0]

    class OpenGL(ConfigNode):

        def __init__(self):
           # camera_position =
           # offset          = (0.0, 0.0, 0.0)
            self.gl_window_size  = [800, 800]
            pass

    class Computation(ConfigNode):
        def __init__(self):
            self.atom_radius     = 2.65
            self.std_resolution  = 64

    class Path(ConfigNode):

        def __init__(self):
            self.result_dir = '../results/'
            self.ffmpeg     = '/usr/local/bin/ffmpeg'

    def __init__(self):
        # standard configuration
        self.Colors          = Configuration.Colors()
        self.OpenGL          = Configuration.OpenGL()
        self.Computation     = Configuration.Computation()
        self.Path            = Configuration.Path()

        self.window_position = [-1, -1]
        self.recent_files    = ['']
        self.max_files       = 5

        self._file = ConfigFile(self)


    def add_recent_file(self, filename):
        if len(self.recent_files) == 1 and not self.recent_files[0]:
            self.recent_files[0] = filename
        elif len(self.recent_files) == self.max_files:
            for i in range(self.max_files - 1):
                self.recent_files[i] = self.recent_files[i + 1]
            self.recent_files[self.max_files - 1] = filename
        else:
            self.append(filename)

    def save(self):
        """
        write configuration to file
        """

        self._file.save()

    def read(self):
        """
        read configuration from file
        """
        self._file = ConfigFile(self)
        self._file.read()


class ConfigFile:
    """
    ConfigFile that parses the settings to a configuration file using ConfigObj 4
    """

    def __init__(self, cfg):
        self.config = cfg

    def generate_configspec(self):
        """
        generates the type specification for the configuration data
        """
        spec_file = configobj.ConfigObj(CONFIG_SPEC_FILE)
        self.generate_spec_for_section(self.file, spec_file)
        spec_file.write()

    def generate_spec_for_section(self, section, spec_section):
        """
        recursive type specification for each subtree
        """
        for scalar in section.scalars:
            t = type(section[scalar])
            type_string = type_dict[t][0] if t is not list else type_dict[type(section[scalar][0])][1] + '_list'
            spec_section[scalar] = type_string
        for sect in section.sections:
            spec_section[sect] = {}
            self.generate_spec_for_section(section[sect], spec_section[sect])

    def save(self):
        """
        recursively reads the object and saves it to the ConfigFile object and finally writes it into the file
        """
        self.file = configobj.ConfigObj(CONFIG_FILE)
        self.parse_node_to_section(self.config, self.file)

        self.file.write()
        self.generate_configspec()
        self.file.write()

    def parse_node_to_section(self, node, section):
        """
        parses a ConfigNode to file object
        """
        for attr_str in dir(node):
            attr = getattr(node, attr_str)
            if isinstance(attr, ConfigNode):
                section[attr.__class__.__name__] = {}
                self.parse_node_to_section(attr, section[attr.__class__.__name__])
            elif not inspect.ismethod(attr) and not attr_str.startswith('_'):
                section[attr_str] = attr
            else:
                pass
                #print attr_str, 'NOT PROCESSED'

    def read(self):
        """
        read a configuration from file
        """
        if not os.path.isfile(CONFIG_SPEC_FILE) or not os.path.isfile(CONFIG_FILE):
            self.save()
        else:
            validator = validate.Validator()
            self.file = configobj.ConfigObj(CONFIG_FILE, configspec=CONFIG_SPEC_FILE)
            self.file.validate(validator)
            self.parse_section_to_node(self.file, self.config)

    def parse_section_to_node(self, section, node):
        """
        parses a config section to config object
        """
        for scalar in section.scalars:
            setattr(node, scalar, section[scalar])
        for sec in section.sections:
            self.parse_section_to_node(section[sec], getattr(node, sec))

config = Configuration()
config.read()

