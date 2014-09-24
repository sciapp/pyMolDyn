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
            self.CAVITY         = [0.2, 0.4, 1.]
            self.DOMAIN         = [0., 1., 0.5]
            self.ALT_CAVITY     = [0.9, 0.4, 0.2]
            self.BACKGROUND     = [0.0, 0.0, 0.0]
            self.BOUNDING_BOX   = [1.0, 1.0, 1.0]
            self.ATOMS          = [1.0, 1.0, 1.0]

    class OpenGL(ConfigNode):

        def __init__(self):
           # CAMERA_POSITION =
           # OFFSET          = (0.0, 0.0, 0.0)
            pass

    class Computation(ConfigNode):
        def __init__(self):
            self.ATOM_RADIUS     = 2.65

    class Path(ConfigNode):

        def __init__(self):
            self.RESULT_DIR = '../results/'
            self.FFMPEG     = '/usr/local/bin/ffmpeg'

    def __init__(self):
        # standard configuration
        self.GL_WINDOW_SIZE  = [800, 800]
        self.WINDOW_POSITION = [-1, -1]
        self.STD_RESOLUTION  = 64
        self.Colors          = Configuration.Colors()
        self.OpenGL          = Configuration.OpenGL()
        self.Computation     = Configuration.Computation()
        self.Path            = Configuration.Path()

        self._file = ConfigFile(self)

    def save(self):
        """
        write configuration to file
        """

        self._file.obj2file()

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

    def obj2file(self):
        """
        recursively reads the object and saves it to the ConfigFile object and finally writes it into the file
        """
        self.file = configobj.ConfigObj(CONFIG_FILE)
        self.parse_node(self.config, self.file)
        self.generate_configspec()
        self.file.write()

    def parse_node(self, cls, config_file):
        """
        parses a class subtree
        """
        for attr_str in dir(cls):
            attr = getattr(cls, attr_str)
            if isinstance(attr, ConfigNode):
                config_file[attr.__class__.__name__] = {}
                self.parse_node(attr, config_file[attr.__class__.__name__])
            elif not inspect.ismethod(attr) and not attr_str.startswith('_'):
                config_file[attr_str] = attr
            else:
                pass
                #print attr_str, 'NOT PROCESSED'

    def read(self):
        """
        read a configuration from file
        """
        if not os.path.isfile(CONFIG_SPEC_FILE) or not os.path.isfile(CONFIG_FILE):
            self.obj2file()
        else:
            validator = validate.Validator()
            self.file = configobj.ConfigObj(CONFIG_FILE, configspec=CONFIG_SPEC_FILE)
            self.file.validate(validator)
            self.parse_section(self.file, self.config)

    def parse_section(self, section, config_obj):
        """
        parses a config section
        """
        for scalar in section.scalars:
            setattr(config_obj, scalar, section[scalar])
        for sec in section.sections:
            self.parse_section(section[sec], getattr(config_obj, sec))

config = Configuration()
config.read()

