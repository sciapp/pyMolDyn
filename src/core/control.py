from config.configuration import config
from core import calculation
import os.path

class Control:

    def __init__(self):
        self.config = config
        if not os.path.isdir(config.Path.result_dir):
            os.mkdir(config.Path.result_dir)
