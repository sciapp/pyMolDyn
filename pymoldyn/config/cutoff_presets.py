# -*- coding: utf-8 -*-

from __future__ import absolute_import

import collections
import json
import os.path
import sys
from .configuration import CONFIG_DIRECTORY
from ..util.logger import Logger

logger = Logger("config.cutoff_presets")
logger.setstream("default", sys.stdout, Logger.WARNING)


DEFAULT_CONFIG_FILE = os.path.expanduser(os.path.join(CONFIG_DIRECTORY, 'cutoff_presets.json'))


Preset = collections.namedtuple('Preset', ['name', 'radii'])


class CutoffPresets(object):
    def __init__(self, config_filepath=DEFAULT_CONFIG_FILE):
        self._config_filepath = config_filepath
        self._presets = None
        self.read()

    def read(self):
        try:
            with open(self._config_filepath, 'r') as f:
                presets_json = json.load(f)
            self._presets = [Preset(*entry) for entry in presets_json]
        except IOError:
            self._presets = []

    def save(self):
        try:
            with open(self._config_filepath, 'w') as f:
                json.dump(self._presets, f)
        except IOError:
            logger.warn('Could not save cutoff radii presets')
            raise

    @property
    def presets(self):
        return list(self._presets)

    def add(self, entry):
        self._presets.insert(0, entry)

    def extend(self, entry_list):
        for entry in entry_list:
            self.add(entry)

    def remove(self, entry):
        self._presets.remove(entry)

    def remove_list(self, entry_list):
        for entry in entry_list:
            self.remove(entry)


cutoff_presets = CutoffPresets()
