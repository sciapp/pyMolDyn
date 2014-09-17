from config import configuration
from core import calculation
import os.path
from config.configuration import config

class Control:

    def __init__(self):
        self.config = config
        config.read()
        if not os.path.isdir(config.RESULT_DIR):
            os.mkdir(config.RESULT_DIR)
