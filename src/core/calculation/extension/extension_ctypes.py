# -*- coding: utf-8 -*-


__all__ = ["atomstogrid"]


import numpy as np
from ctypes import c_int, c_int64, c_int8, POINTER, sizeof, CDLL
import sys
import os


if sys.platform == "win32":
    libext = ".dll"
else:
    libext = ".so"

libpath = os.path.join(os.path.realpath(os.path.dirname(__file__)), "libalgorithm"+libext)
lib = CDLL(libpath)

lib.atomstogrid.restype = None
lib.atomstogrid.argtypes = [
        POINTER(c_int64), # grid
        c_int * 3,        # dimensions
        c_int * 3,        # strides
        c_int,            # natoms
        POINTER(c_int),   # atom_positions
        POINTER(c_int),   # radii_indices
        c_int,            # nradii
        POINTER(c_int),   # radii
        c_int,            # ntranslations
        POINTER(c_int),   # translations
        POINTER(c_int8),  # discretization_grid
        c_int * 3]        # discretization_grid_strides



def atomstogrid(grid, discrete_positions, radii_indices, discrete_radii, translation_vectors, discretization_grid):
    int_type = np.dtype(c_int)

    dimensions = (c_int * 3)(*grid.shape)
    strides = (c_int * 3)(*[s / grid.itemsize for s in grid.strides])
    grid_p = grid.ctypes.data_as(POINTER(c_int64))

    discrete_positions = np.ascontiguousarray(discrete_positions, dtype=int_type)
    natoms = c_int(discrete_positions.shape[0])
    discrete_positions_p = discrete_positions.ctypes.data_as(POINTER(c_int))

    radii_indices = np.ascontiguousarray(radii_indices, dtype=int_type)
    radii_indices_p = radii_indices.ctypes.data_as(POINTER(c_int))

    discrete_radii = np.ascontiguousarray(discrete_radii, dtype=int_type)
    nradii = discrete_radii.shape[0]
    discrete_radii_p = discrete_radii.ctypes.data_as(POINTER(c_int))

    translation_vectors = np.ascontiguousarray(translation_vectors, dtype=int_type)
    ntranslations = c_int(translation_vectors.shape[0])
    translation_vectors_p = translation_vectors.ctypes.data_as(POINTER(c_int))

    discretization_grid_strides = (c_int * 3)(*[s / discretization_grid.itemsize for s in discretization_grid.strides])
    discretization_grid_p = discretization_grid.ctypes.data_as(POINTER(c_int8))

    lib.atomstogrid(grid_p, dimensions, strides,
            natoms, discrete_positions_p, radii_indices_p,
            nradii, discrete_radii_p,
            ntranslations, translation_vectors_p,
            discretization_grid_p, discretization_grid_strides)

