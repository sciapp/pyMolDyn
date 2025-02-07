import sys

from pymoldyn.util import env_is_true, message
from pymoldyn.util.logger import Logger

__all__ = [
    "atomstogrid",
    "mark_cavities",
    "cavity_triangles",
    "cavity_intersections",
    "mark_translation_vectors",
]

logger = Logger("core.calculation")
logger.setstream("default", sys.stdout, Logger.WARNING)


class CExtensionError(Exception):
    pass


try:
    from .extension_ctypes import (
        atomstogrid,
        cavity_intersections,
        cavity_triangles,
        mark_cavities,
        mark_translation_vectors,
    )
except OSError as e:
    if env_is_true("PYMOLDYN_FORCE_EXTENSIONS"):
        logger.error(e.__repr__())
        logger.error("C extension could not be loaded")
        message.log("C extension could not be loaded, aborting!")
        raise CExtensionError('"algorithm" C extension could not be loaded') from e
    else:
        logger.warn(e.__repr__())
        logger.warn("Falling back to Python functions")
        message.log(
            "C extensions could not be loaded, falling back to Python functions. Calculations may be very slow!"
        )
        from .extension_python import (
            atomstogrid,
            cavity_intersections,
            cavity_triangles,
            mark_cavities,
            mark_translation_vectors,
        )
