# -*- coding: utf-8 -*-


import os.path
import threading
from config.configuration import config
import core.calculation as calculation
import visualization


# TODO: make an instance of this available everywhere


class Control:

    def __init__(self):
        self.config = config
        if not os.path.isdir(config.Path.result_dir):
            os.mkdir(config.Path.result_dir)
        self._calculation = calculation.Calculation()
        self._visualization = None # will be initialized when needed
        self.results = None
        self.calculationcallback = Control.defaultcallback
        self.lock = threading.Lock()

    def _calculate(self, settings):
        with self.lock:
            self.results = None
            self.results = self.calculation.calculate(settings)

    def calculate(self, settings):
        self.calculationcallback(self._calculate, settings.copy())

    def update(self):
        with self.lock:
            if len(self.results) > 0:
                self.visualization.setresults(self.results[-1][-1])

    @staticmethod
    def defaultcallback(func, settings):
        func(settings)

    @property
    def calculation(self):
        return self._calculation

    @property
    def visualization(self):
        if self._visualization is None:
            self._visualization = visualization.Visualization()
        return self._visualization
