# -*- coding: utf-8 -*-


from core.control import Control
from cli import Cli


def start():
    control = Control()
    instance = Cli(control)
    #controller.register_view(instance, Attributes.CLI_ATTRIBUTES)
    instance.start()


if __name__ == '__main__':
    start()
