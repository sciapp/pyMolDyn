# -*- coding: utf-8 -*-

import os
from core.control import Control
from cli import Cli


def start():
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    control = Control()
    instance = Cli(control)
    #controller.register_view(instance, Attributes.CLI_ATTRIBUTES)
    instance.start()


if __name__ == '__main__':
    start()
