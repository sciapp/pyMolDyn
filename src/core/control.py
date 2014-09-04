from config import configuration
from core import calculation
from config.configuration import config

class Control:

    def __init__(self):
        self.config = config
        config.read()
