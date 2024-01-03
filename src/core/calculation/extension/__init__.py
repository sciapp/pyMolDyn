# -*- coding: utf-8 -*-

import sys
from util import message
from util.logger import Logger

__all__ = ["atomstogrid",
           "mark_cavities",
           "cavity_triangles",
           "cavity_intersections",
           "mark_translation_vectors"]

logger = Logger("core.calculation")
logger.setstream("default", sys.stdout, Logger.WARNING)

try:
    from .extension_ctypes import atomstogrid, \
                                 mark_cavities, \
                                 cavity_triangles, \
                                 cavity_intersections, \
                                 mark_translation_vectors
except OSError as e:
    logger.warn(e.__repr__())
    logger.warn("Falling back to Python functions")
    message.log("C extensions could not be loaded, falling back to Python functions. Calculations may be very slow!")
    from .extension_python import atomstogrid, \
                                 mark_cavities, \
                                 cavity_triangles, \
                                 cavity_intersections, \
                                 mark_translation_vectors
