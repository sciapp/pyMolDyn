#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

import gr
import numpy as np

sys.path.insert(0, os.path.abspath("../src"))
from statistics.rdf import Kernels

x = np.linspace(-1.25, 1.25, 500)
for name in dir(Kernels):
    if name.startswith("_") or name == "bandwidth":
        continue
    kernel = getattr(Kernels, name)
    y = kernel(x)
    gr.beginprint(name.lower() + ".svg")
    gr.clearws()
    gr.setwsviewport(0, 0.1, 0, 0.06)
    gr.setviewport(0, 1, 0, 1)
    gr.setwindow(-1.25, 1.25, -0.25, 1.25)
    gr.grid(0.1, 0.1, 0, 0, 5, 5)
    gr.axes(0.1, 0.1, 0, 0, 5, 5, -0.01)
    gr.setlinewidth(2)
    gr.setlinecolorind(2)
    gr.polyline(x, y)
    gr.setlinecolorind(1)
    gr.setlinewidth(1)
    gr.updatews()
    gr.endprint()
