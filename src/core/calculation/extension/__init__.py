# -*- coding: utf-8 -*-


__all__ = ["atomstogrid",
           "mark_cavities",
           "cavity_triangles",
           "cavity_intersections"]

try:
    from extension_ctypes import atomstogrid, mark_cavities, cavity_triangles, cavity_intersections
except OSError as e:
    print e.__repr__()
    print "Falling back to Python functions"
    from extension_python import atomstogrid, mark_cavities, cavity_triangles, cavity_intersections

