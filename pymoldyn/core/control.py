"""
The :class:`Control` object is the central part of pyMolDyn.
It is responsible for initiating the calculation process and visualizing
the results.
It contains instances of :class:`core.calculation.calculation.Calculation` and
:class:`visualization.visualization.Visualization` and manages the
interaction between them.

The calculation can be started in an different thread. To do that,
the ``calculationcallback`` attribute can be set
to a custom function. This custom function has to take two parameters:
``func`` and ``settings``, and has to call ``func`` with the parameter
``settings``. Here is an easy example::

    def callback(func, settings):
        func(settings)

    control.calculationcallback = callback

And with threads::

    class CalculationThread(QtCore.QThread):
        def __init__(self, parent, func, settings):
            QtCore.QThread.__init__(self, parent)
            self.func = func
            self.settings = settings

        def run(self):
            self.func(self.settings)

    class GUI:
        def __init__(self, ...):
            ...
            self.control.calculationcallback = self.calculationcallback

        def calculationcallback(self, func, settings):
            thread = CalculationThread(self, func, settings)
            thread.finished.connect(self.control.update)
            thread.start()
"""

import os.path
import threading

from .. import visualization
from ..config.configuration import config
from ..core import calculation as calculation

# TODO: make an instance of this available everywhere


class Control(object):
    """
    The central controller class that contains the application logic.
    It contains the following attributes:

        `calculation` : :class:`core.calculation.calculation.Calculation`

        `visualization` : :class:`visualization.visualization.Visualization`
    """

    def __init__(self):
        self.config = config
        if not os.path.isdir(os.path.expanduser(config.Path.cache_dir)):
            os.makedirs(os.path.expanduser(config.Path.cache_dir))
        self._calculation = calculation.Calculation()
        self._visualization = None  # will be initialized when needed
        self.results = None
        self.calculationcallback = Control.defaultcallback
        self.lock = threading.Lock()

    def _calculate(self, settings):
        with self.lock:
            self.results = None
            self.results = self.calculation.calculate(settings)

    def calculate(self, settings):
        """
        Start a calculation and create prepare the results to be visualized.
        To make it possible to start the calculation in a thread, the
        function ``self.calculation`` is called, which then starts the
        calculation itself.

        **Parameters:**
            `settings` :
                :class:`core.calculation.calculation.CalculationSettings` object
        """
        # TODO: only call when something is calculated
        self.calculationcallback(self._calculate, settings.copy())

    def update(self, was_successful=lambda: True):
        """
        Visualize previously calculated results. It has to be called from
        the same thread which uses the OpenGL context, usually the
        event handler of the GUI.
        """
        with self.lock:
            if was_successful and self.results is not None:
                self.visualization.setresults(self.results[-1][-1])

    def visualize(self, filename, frame, resolution=None):
        """
        Visualize the given frame. if the ``resolution`` parameter is not set,
        this function uses the highest resolution available to show
        calculation results.
        """
        results = self.calculation.getresults(filename, frame, resolution)
        self.results = [[results]]
        self.update()

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
