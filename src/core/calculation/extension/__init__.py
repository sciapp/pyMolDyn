# -*- coding: utf-8 -*-


__all__ = ["atomstogrid",
           "mark_cavities",
           "cavity_triangles"]

try:
    from extension_ctypes import atomstogrid, mark_cavities
except OSError as e:
    print e.__repr__()
    print "Falling back to Python functions"
    from extension_python import atomstogrid, mark_cavities

from extension_python import cavity_triangles as cavity_triangles_py
from extension_ctypes import cavity_triangles as cavity_triangles_c

def cavity_triangles(grid3,
        cavity_indices,
        step, offset,
        discretization_grid):
    vertices_c, normals_c, surface_area_c = cavity_triangles_c(
            grid3,
            cavity_indices,
            step, offset,
            discretization_grid)
    vertices_py, normals_py, surface_area_py = cavity_triangles_py(
            grid3,
            cavity_indices,
            step, offset,
            discretization_grid)

    print vertices_c.shape[0], surface_area_c, vertices_py.shape[0], surface_area_py
    
    #return vertices_c, normals_c, surface_area_c
    return vertices_py, normals_py, surface_area_py

