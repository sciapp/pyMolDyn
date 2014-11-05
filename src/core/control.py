# -*- coding: utf-8 -*-
from config.configuration import config
from core import calculation
import os.path


# TODO: create Calculation object
# TODO: make an instance of this available everywhere


class Control:

    def __init__(self):
        self.config = config
        if not os.path.isdir(config.Path.result_dir):
            os.mkdir(config.Path.result_dir)
