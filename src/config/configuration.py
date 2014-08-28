import configobj
import validate
import os.path
import inspect

CONFIG_FILE = 'config.cfg'
CONFIG_SPEC_FILE = 'config.spec'

# second string is the list type name
type_dict = {
    int: ('integer', 'int'),
    float: ('float', 'float'),
    str: ('string', 'string'),
    bool: ('boolean', 'bool')
}


class Configuration:

    # standard configuration
    RESULT_DIR      = '../results/'
    GL_WINDOW_SIZE  = (800, 800)
    WINDOW_POSITION = (-1, -1)
    STD_RESOLUTION  = 64

    class Colors:
        CAVITY          = (0.2, 0.4, 1)
        DOMAIN          = (0, 1, 0.5)
        ALT_CAVITY      = (0.9, 0.4, 0.2)
        BACKGROUND      = (0.0, 0.0, 0.0)
        BOUNDING_BOX    = (1.0, 1.0, 1.0)

    class OpenGL:
       # CAMERA_POSITION =
       # OFFSET          = (0.0, 0.0, 0.0)
        ATOM_RADIUS     = 2.8

    def __init__(self):
        self.file = ConfigFile(self)

    def save(self):
        self.file.write()

    def read(self):
        self.file.read()

class ConfigFile:

    def __init__(self, config):
        self.config = config
        self.read()

    def write(self):
        self.file.write()

    def generate_configspec(self):
        spec_file = configobj.ConfigObj(CONFIG_SPEC_FILE)
        self.generate_spec_for_section(self.file, spec_file)
        spec_file.write()

    def generate_spec_for_section(self, section, spec_section):
        for scalar in section.scalars:
            t = type(section[scalar])
            type_string = type_dict[t][0] if t is not list else type_dict[type(section[scalar][0])][1]+'_list'
            spec_section[scalar] = type_string
        for sect in section.sections:
            spec_section[sect] = {}
            self.generate_spec_for_section(section[sect], spec_section[sect])

    def obj2file(self):
        self.file = configobj.ConfigObj(CONFIG_FILE)
        for attr in dir(self.config):
            if inspect.isclass(attr):
                #TODO incomplete
                pass


    def read(self):
        if not os.path.isfile(CONFIG_SPEC_FILE):
            pass                                        #TODO in case spec file does not exist
        validator = validate.Validator()
        self.file = configobj.ConfigObj(CONFIG_FILE, configspec=CONFIG_SPEC_FILE)
        self.file.validate(validator)
        self.parse_section(self.file, self.config)

    def parse_section(self, section, config_obj):
        for scalar in section.scalars:
            setattr(config_obj, scalar, section[scalar])
        for sec in section.sections:
            self.parse_section(sec, getattr(self.config, sec))
