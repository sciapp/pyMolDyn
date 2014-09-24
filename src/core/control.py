from config import configuration
from core import calculation
import os.path
from config.configuration import config

class Control:

    def __init__(self):
        self.config = config
        if not os.path.isdir(config.Path.RESULT_DIR):
            os.mkdir(config.Path.RESULT_DIR)
