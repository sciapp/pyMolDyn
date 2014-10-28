# -*- coding: utf-8 -*-
from config import configuration
from core import calculation
import os.path
from config.configuration import config


# TODO: create Calculation object
# TODO: make an instance of this available everywhere


class Control:

    def __init__(self):
        self.config = config
        if not os.path.isdir(config.Path.result_dir):
            os.mkdir(config.Path.result_dir)
