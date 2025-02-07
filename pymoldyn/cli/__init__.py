import os

from ..core import file
from ..core.control import Control
from .cli import Cli

__all__ = ["Cli"]


def main():
    file.SEARCH_PATH = os.getcwd()
    os.chdir(os.path.abspath(os.path.dirname(__file__)))
    control = Control()
    instance = Cli(control)
    instance.start()


if __name__ == "__main__":
    main()
