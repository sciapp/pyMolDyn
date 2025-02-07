__all__ = ["atomstogrid", "mark_cavities", "cavity_triangles", "cavity_intersections"]


import os
import platform
from ctypes import CDLL, POINTER, Structure, byref, c_float, c_int, c_int8, c_int64, cast

# Import gr3 to load `libGR3.so` which is needed by the ctypes extension
import gr3  # noqa: F401 pylint: disable=unused-import
import numpy as np

int_type = np.dtype(c_int)


class subgrid_cell_t(Structure):
    _fields_ = [
        ("num_atoms", c_int),
        ("atom_positions", POINTER(c_int)),
        ("num_domains", c_int),
        ("domain_indices", POINTER(c_int)),
        ("domain_positions", POINTER(c_int)),
    ]


class subgrid_t(Structure):
    _fields_ = [
        ("subgrid_cell_t", POINTER(subgrid_cell_t)),
        ("cubesize", c_int),
        ("ncells", c_int),
        ("dimensions", c_int * 3),
        ("strides", c_int * 3),
    ]


shared_lib_prefix = {
    "Windows": "",
}.get(platform.system(), "lib")

shared_lib_ext = {
    "Darwin": ".dylib",
    "Windows": ".dll",
}.get(platform.system(), ".so")

libpath = os.path.join(
    os.path.realpath(os.path.dirname(__file__)),
    shared_lib_prefix + "algorithm" + shared_lib_ext,
)
lib = CDLL(libpath)

lib.atomstogrid.restype = None
lib.atomstogrid.argtypes = [
    POINTER(c_int64),  # grid
    c_int * 3,  # dimensions
    c_int * 3,  # strides
    c_int,  # natoms
    POINTER(c_int),  # atom_positions
    POINTER(c_int),  # radii_indices
    c_int,  # nradii
    POINTER(c_int),  # radii
    c_int,  # ntranslations
    POINTER(c_int),  # translations
    POINTER(c_int8),  # discretization_grid
    c_int * 3,
]  # discretization_grid_strides

lib.subgrid_create.restype = POINTER(subgrid_t)
lib.subgrid_create.argtypes = [c_int, c_int * 3]  # cubesize  # grid_dimensions

lib.subgrid_destroy.restype = None
lib.subgrid_destroy.argtypes = [POINTER(subgrid_t)]  # sg

lib.subgrid_add_atoms.restype = None
lib.subgrid_add_atoms.argtypes = [
    POINTER(subgrid_t),  # sg
    c_int,  # natoms
    POINTER(c_int),  # atom_positions
    c_int,  # ntranslations
    POINTER(c_int),
]  # translations

lib.subgrid_add_domains.restype = None
lib.subgrid_add_domains.argtypes = [
    POINTER(subgrid_t),  # sg
    c_int,  # npoints
    POINTER(c_int),  # domain_indices
    POINTER(c_int),  # domain_points
    c_int,  # ntranslations
    POINTER(c_int),
]  # translations

lib.mark_cavities.restype = None
lib.mark_cavities.argtypes = [
    POINTER(c_int64),  # grid
    POINTER(c_int64),  # domain_grid
    c_int * 3,  # dimensions
    c_int * 3,  # strides
    POINTER(c_int8),  # discretization_grid
    c_int * 3,  # discgrid_strides
    POINTER(subgrid_t),  # sg
    c_int,
]  # use_surface_points

lib.cavity_triangles.restype = c_int
lib.cavity_triangles.argtypes = [
    POINTER(c_int64),  # cavity_grid
    c_int * 3,  # dimensions
    c_int * 3,  # strides
    c_int,  # ncavity_indices
    POINTER(c_int),  # cavity_indices
    c_int,  # isolevel
    c_float * 3,  # step
    c_float * 3,  # offset
    POINTER(c_int8),  # discretization_grid
    c_int * 3,  # discgrid_strides
    POINTER(POINTER(c_float)),  # vertices
    POINTER(POINTER(c_float)),  # normals
    POINTER(c_float),
]  # surface_area

lib.free_float_p.restype = None
lib.free_float_p.argtypes = [POINTER(c_float)]

lib.cavity_intersections.restype = None
lib.cavity_intersections.argtypes = [
    POINTER(c_int64),  # grid
    c_int * 3,  # dimensions
    c_int * 3,  # strides
    c_int,  # num_domains
    POINTER(c_int8),
]  # intersection_table

lib.mark_translation_vectors.restype = None
lib.mark_translation_vectors.argtypes = [
    POINTER(c_int8),  # grid
    c_int * 3,  # dimensions
    c_int * 3,  # strides
    c_int,  # ntranslations
    POINTER(c_int),
]  # translations


def atomstogrid(
    grid,
    discrete_positions,
    radii_indices,
    discrete_radii,
    translation_vectors,
    discretization_grid,
):
    dimensions = (c_int * 3)(*grid.shape)
    strides = (c_int * 3)(*[s // grid.itemsize for s in grid.strides])
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

    discretization_grid_strides = (c_int * 3)(*[s // discretization_grid.itemsize for s in discretization_grid.strides])
    discretization_grid_p = discretization_grid.ctypes.data_as(POINTER(c_int8))

    lib.atomstogrid(
        grid_p,
        dimensions,
        strides,
        natoms,
        discrete_positions_p,
        radii_indices_p,
        nradii,
        discrete_radii_p,
        ntranslations,
        translation_vectors_p,
        discretization_grid_p,
        discretization_grid_strides,
    )


def subgrid_create(cubesize, grid_dimensions):
    cubesize_c = c_int(cubesize)
    grid_dimensions_c = (c_int * 3)(*grid_dimensions)
    sg = lib.subgrid_create(cubesize_c, grid_dimensions_c)
    return sg


def subgrid_destroy(sg):
    lib.subgrid_destroy(sg)


def subgrid_add_atoms(sg, atom_positions, translation_vectors):
    atom_positions = np.ascontiguousarray(atom_positions, dtype=int_type)
    natoms_c = c_int(atom_positions.shape[0])
    atom_positions_c = atom_positions.ctypes.data_as(POINTER(c_int))

    translations = np.ascontiguousarray(translation_vectors, dtype=int_type)
    ntranslations_c = c_int(translations.shape[0])
    translations_c = translations.ctypes.data_as(POINTER(c_int))

    lib.subgrid_add_atoms(sg, natoms_c, atom_positions_c, ntranslations_c, translations_c)


def subgrid_add_domains(sg, domain_indices, domain_points, translation_vectors):
    domain_indices = np.ascontiguousarray(domain_indices, dtype=int_type)
    npoints_c = c_int(domain_indices.shape[0])
    domain_indices_c = domain_indices.ctypes.data_as(POINTER(c_int))

    domain_points = np.ascontiguousarray(domain_points, dtype=int_type)
    domain_points_c = domain_points.ctypes.data_as(POINTER(c_int))

    translations = np.ascontiguousarray(translation_vectors, dtype=int_type)
    ntranslations_c = c_int(translations.shape[0])
    translations_c = translations.ctypes.data_as(POINTER(c_int))

    lib.subgrid_add_domains(
        sg,
        npoints_c,
        domain_indices_c,
        domain_points_c,
        ntranslations_c,
        translations_c,
    )


def mark_cavities_c(grid, domain_grid, discretization_grid, sg, use_surface_points):
    dimensions_c = (c_int * 3)(*grid.shape)
    strides_c = (c_int * 3)(*[s // grid.itemsize for s in grid.strides])
    grid_c = grid.ctypes.data_as(POINTER(c_int64))

    if domain_grid is not None:
        domain_grid_c = domain_grid.ctypes.data_as(POINTER(c_int64))
    else:
        domain_grid_c = POINTER(c_int64)()

    discgrid_strides_c = (c_int * 3)(*[s // discretization_grid.itemsize for s in discretization_grid.strides])
    discretization_grid_c = discretization_grid.ctypes.data_as(POINTER(c_int8))

    use_surface_points_c = c_int(use_surface_points)

    lib.mark_cavities(
        grid_c,
        domain_grid_c,
        dimensions_c,
        strides_c,
        discretization_grid_c,
        discgrid_strides_c,
        sg,
        use_surface_points_c,
    )


def mark_cavities(
    domain_grid,
    discretization_grid,
    grid_dimensions,
    sg_cube_size,
    atom_positions,
    translation_vectors,
    domain_point_list,
    use_surface_points,
):

    # step 1
    sg = subgrid_create(sg_cube_size, grid_dimensions)
    # step 2
    subgrid_add_atoms(sg, atom_positions, translation_vectors)

    # step 3
    domain_indices = []
    domain_points = []
    for i in range(len(domain_point_list)):
        for p in domain_point_list[i]:
            domain_indices.append(i)
            domain_points.append(p)
    subgrid_add_domains(sg, domain_indices, domain_points, translation_vectors)

    grid = np.zeros(grid_dimensions, dtype=np.int64)
    # step 4 and 5
    mark_cavities_c(grid, domain_grid, discretization_grid, sg, use_surface_points)

    subgrid_destroy(sg)

    return grid


def cavity_triangles(cavity_grid, cavity_indices, isolevel, step, offset, discretization_grid):
    cavity_grid_c = cavity_grid.ctypes.data_as(POINTER(c_int64))
    dimensions_c = (c_int * 3)(*cavity_grid.shape)
    strides_c = (c_int * 3)(*[s // cavity_grid.itemsize for s in cavity_grid.strides])

    if not isinstance(cavity_indices, np.ndarray) and not isinstance(cavity_indices, list):
        cavity_indices = list(cavity_indices)
    ncavity_indices_c = c_int(len(cavity_indices))
    cavity_indices = np.ascontiguousarray(cavity_indices, dtype=int_type)
    cavity_indices_c = cavity_indices.ctypes.data_as(POINTER(c_int))

    isolevel_c = c_int(isolevel)
    step_c = (c_float * 3)(*step)
    offset_c = (c_float * 3)(*offset)

    discretization_grid_c = discretization_grid.ctypes.data_as(POINTER(c_int8))
    discgrid_strides_c = (c_int * 3)(*[s // discretization_grid.itemsize for s in discretization_grid.strides])

    vertices_c = POINTER(c_float)()
    normals_c = POINTER(c_float)()
    surface_area_c = c_float()

    ntriangles = lib.cavity_triangles(
        cavity_grid_c,
        dimensions_c,
        strides_c,
        ncavity_indices_c,
        cavity_indices_c,
        isolevel_c,
        step_c,
        offset_c,
        discretization_grid_c,
        discgrid_strides_c,
        byref(vertices_c),
        byref(normals_c),
        byref(surface_area_c),
    )

    ArrayType = c_float * ntriangles * 3 * 3
    vertices_p = cast(vertices_c, POINTER(ArrayType))
    vertices = np.frombuffer(vertices_p.contents, dtype=c_float)
    vertices = np.array(vertices, dtype=float, copy=True).reshape((ntriangles, 3, 3))
    lib.free_float_p(vertices_c)
    normals_p = cast(normals_c, POINTER(ArrayType))
    normals = np.frombuffer(normals_p.contents, dtype=c_float)
    normals = np.array(normals, dtype=float, copy=True).reshape((ntriangles, 3, 3))
    lib.free_float_p(normals_c)
    surface_area = surface_area_c.value

    return vertices, normals, surface_area


def cavity_intersections(grid, num_domains):
    dimensions_c = (c_int * 3)(*grid.shape)
    strides_c = (c_int * 3)(*[s // grid.itemsize for s in grid.strides])
    grid_c = grid.ctypes.data_as(POINTER(c_int64))

    num_domains_c = c_int(num_domains)
    intersection_table = np.zeros((num_domains, num_domains), dtype=np.int8)
    intersection_table_c = intersection_table.ctypes.data_as(POINTER(c_int8))

    lib.cavity_intersections(grid_c, dimensions_c, strides_c, num_domains_c, intersection_table_c)

    return intersection_table


def mark_translation_vectors(grid, translation_vectors):
    dimensions_c = (c_int * 3)(*grid.shape)
    strides_c = (c_int * 3)(*[s // grid.itemsize for s in grid.strides])
    grid_c = grid.ctypes.data_as(POINTER(c_int8))

    translation_vectors = np.ascontiguousarray(translation_vectors, dtype=int_type)
    ntranslations_c = c_int(translation_vectors.shape[0])
    translation_vectors_c = translation_vectors.ctypes.data_as(POINTER(c_int))

    lib.mark_translation_vectors(grid_c, dimensions_c, strides_c, ntranslations_c, translation_vectors_c)
