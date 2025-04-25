import inspect
import os
import os.path

from ..util.logger import Logger
from . import configobj, validate

logger = Logger("config.configuration")

# MUST be written with ~ to save a path in the config file that is relative to the user's home directory
CONFIG_DIRECTORY = "~/.pymoldyn/"
CONFIG_FILE = os.path.expanduser("%s/config.cfg" % CONFIG_DIRECTORY)
CONFIG_SPEC_FILE = os.path.expanduser("%s/config.spec" % CONFIG_DIRECTORY)

# second string is the list type name
type_dict = {
    int: ("integer", "int"),
    float: ("float", "float"),
    str: ("string", "string"),
    str: ("string", "string"),
    bool: ("boolean", "bool"),
}


class ConfigNode(object):

    def __init__(self):
        pass


class Configuration(ConfigNode):
    """
    Configuration Object that contains the application settings
    """

    class Colors(ConfigNode):

        def __init__(self):
            self.surface_cavity = [0.2, 0.4, 1.0]
            self.domain = [0.0, 1.0, 0.5]
            self.center_cavity = [0.9, 0.4, 0.2]
            self.background = [0.0, 0.0, 0.0]
            self.bounding_box = [1.0, 1.0, 1.0]
            self.bonds = [0.8, 0.8, 0.8]

    class OpenGL(ConfigNode):

        def __init__(self):
            # camera_position =
            # offset          = (0.0, 0.0, 0.0)
            self.gl_window_size = [1200, 400]
            self.atom_radius = 0.4
            self.bond_radius = 0.1
            pass

    class Computation(ConfigNode):
        def __init__(self):
            self.std_cutoff_radius = 2.8
            self.std_resolution = 64
            self.max_cachefiles = 0

    class Path(ConfigNode):

        def __init__(self):
            self.cache_dir = os.path.join(CONFIG_DIRECTORY, "cache")
            self.ffmpeg = "/usr/local/bin/ffmpeg"
            self.result_dir = os.path.join(CONFIG_DIRECTORY, "results")

    def __init__(self):
        # standard configuration
        self.Colors = Configuration.Colors()
        self.OpenGL = Configuration.OpenGL()
        self.Computation = Configuration.Computation()
        self.Path = Configuration.Path()

        self.window_position = [-1, -1]
        self.recent_files = [""]
        self.max_files = 5

        self._file = ConfigFile(self)

    def add_recent_file(self, filename):
        if len(self.recent_files) == 1 and not self.recent_files[0]:
            self.recent_files[0] = filename
        elif len(self.recent_files) == self.max_files:
            self.recent_files.pop(-1)
            self.recent_files.insert(0, filename)
        else:
            self.recent_files.insert(0, filename)
        self.save()

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


class ConfigFile(object):
    """
    ConfigFile that parses the settings to a configuration file using ConfigObj 4
    """

    def __init__(self, cfg):
        self.config = cfg

    @staticmethod
    def _create_needed_parent_directories(filename):
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def generate_configspec(self):
        """
        generates the type specification for the configuration data
        """
        spec_file = configobj.ConfigObj(CONFIG_SPEC_FILE)
        self.generate_spec_for_section(self.file, spec_file)
        try:
            self._create_needed_parent_directories(CONFIG_SPEC_FILE)
            spec_file.write()
        except PermissionError:
            logger.err("Missing permission to write to %s" % CONFIG_SPEC_FILE)
        except FileNotFoundError:
            logger.err("%s does not exist" % CONFIG_SPEC_FILE)
        except IOError as e:
            logger.err("IOError in ConfigFile.generate_configspec: %s" % e)

    def generate_spec_for_section(self, section, spec_section):
        """
        recursive type specification for each subtree
        """
        for scalar in section.scalars:
            t = type(section[scalar])
            type_string = type_dict[t][0] if t is not list else type_dict[type(section[scalar][0])][1] + "_list"
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

        try:
            self._create_needed_parent_directories(CONFIG_FILE)
            self.file.write()
            self.generate_configspec()
            self.file.write()

        except PermissionError:
            logger.err("Missing permission to write to %s" % CONFIG_FILE)
        except FileNotFoundError:
            logger.err("%s does not exist" % CONFIG_FILE)
        except IOError as e:
            logger.err("IOError in ConfigFile.save: %s" % e)

    def parse_node_to_section(self, node, section):
        """
        parses a ConfigNode to file object
        """
        for attr_str in dir(node):
            attr = getattr(node, attr_str)
            if isinstance(attr, ConfigNode):
                section[type(attr).__name__] = {}
                self.parse_node_to_section(attr, section[type(attr).__name__])
            elif not inspect.ismethod(attr) and not attr_str.startswith("_"):
                section[attr_str] = attr
            else:
                logger.info(f"{attr_str} not processed because it is a method or private attribute")

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
