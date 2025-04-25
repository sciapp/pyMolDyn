__all__ = ["atomstogrid", "mark_cavities", "cavity_triangles", "cavity_intersections"]


import itertools
import sys
from math import ceil

import numpy as np
from gr3 import triangulate

dimension = 3
dimensions = range(dimension)


def atomstogrid(
    grid,
    discrete_positions,
    radii_indices,
    discrete_radii,
    translation_vectors,
    discretization_grid,
):
    last_radius_index = -1  # (for reuse of sphere grids)
    atom_information = zip(range(len(discrete_positions)), radii_indices, discrete_positions)
    for atom_index, radius_index, real_discrete_position in atom_information:
        discrete_radius = discrete_radii[radius_index]
        cube_size = 2 * discrete_radius + 1
        if radius_index != last_radius_index:
            last_radius_index = radius_index
            cube_indices = np.indices([cube_size] * 3).transpose(1, 2, 3, 0) - discrete_radius
            sphere_grid = np.sum(cube_indices**2, axis=3) <= discrete_radius**2
            last_radius_index = radius_index
        for v in translation_vectors:
            discrete_position = [real_discrete_position[i] + v[i] for i in dimensions]
            for point in itertools.product(range(discrete_radius * 2 + 1), repeat=dimension):
                if sphere_grid[point]:
                    p = [point[i] - discrete_radius + discrete_position[i] for i in dimensions]
                    if all([0 <= p[i] <= grid.shape[i] - 1 for i in dimensions]):
                        discretization_grid_value = discretization_grid[tuple(p)]
                        if discretization_grid_value == 0:
                            grid_value = grid[tuple(p)]
                            # check if the atom is the closest one
                            if grid_value == 0:
                                grid[tuple(p)] = atom_index + 1
                            else:
                                this_squared_distance = sum([(x - y) ** 2 for x, y in zip(discrete_position, p)])
                                other_position = discrete_positions[grid_value - 1]
                                for v2 in translation_vectors:
                                    other_discrete_position = [other_position[i] + v2[i] for i in dimensions]
                                    other_squared_distance = sum(
                                        [(x - y) ** 2 for x, y in zip(other_discrete_position, p)]
                                    )
                                    if other_squared_distance <= this_squared_distance:
                                        break
                                if this_squared_distance < other_squared_distance:
                                    grid[tuple(p)] = atom_index + 1


class Subgrid(object):
    def __init__(self, cubesize, grid_dimensions):
        self.cubesize = cubesize
        self.sgd = tuple([2 + int(ceil(1.0 * d / cubesize)) + 2 for d in grid_dimensions])
        self.sg = []
        for x in range(self.sgd[0]):
            self.sg.append([])
            for y in range(self.sgd[1]):
                self.sg[x].append([])
                for z in range(self.sgd[2]):
                    self.sg[x][y].append([[], [], []])  # SEG fault was here

    def add_atoms(self, atom_positions, translation_vectors):
        for atom_index, atom_position in enumerate(atom_positions):
            for v in translation_vectors:
                real_atom_position = [atom_position[i] + v[i] for i in dimensions]
                sgp = self.to_subgrid(real_atom_position)
                self.sg[sgp[0]][sgp[1]][sgp[2]][0].append(real_atom_position)

    def add_domains(self, domain_point_list, translation_vectors):
        for domain_index, domain_seed_points in enumerate(domain_point_list):
            for domain_seed_point in domain_seed_points:
                for v in translation_vectors:
                    real_domain_seed_point = [domain_seed_point[i] + v[i] for i in dimensions]
                    sgp = self.to_subgrid(real_domain_seed_point)
                    self.sg[sgp[0]][sgp[1]][sgp[2]][1].append(real_domain_seed_point)
                    self.sg[sgp[0]][sgp[1]][sgp[2]][2].append(domain_index)

    def to_subgrid(self, position):
        sgp = [c // self.cubesize + 2 for c in position]
        for i in dimensions:
            if sgp[i] < 0:
                sgp[i] = 0
            if sgp[i] >= self.sgd[i]:
                sgp[i] = self.sgd[i] - 1
        return tuple(sgp)


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

    # steps 1 to 3
    sg = Subgrid(sg_cube_size, grid_dimensions)
    sg.add_atoms(atom_positions, translation_vectors)
    sg.add_domains(domain_point_list, translation_vectors)

    # step 4
    grid = np.zeros(grid_dimensions, dtype=np.int64)
    for p in itertools.product(*map(range, grid_dimensions)):
        if use_surface_points:
            grid_value = domain_grid[p]
            if grid_value == 0:  # outside the volume
                grid[p] = 0
                possibly_in_cavity = False
            elif grid_value < 0:  # cavity domain (stored as: -index-1), therefore guaranteed to be in a cavity
                grid[p] = grid_value
                possibly_in_cavity = False  # is already marked
            elif grid_value > 0:  # in radius of atom (stored as: index+1), therefore possibly in a cavity
                grid[p] = 0
                possibly_in_cavity = True
        else:
            possibly_in_cavity = discretization_grid[p] == 0
        if possibly_in_cavity:
            # step 5
            min_squared_atom_distance = sys.maxsize
            sgp = sg.to_subgrid(p)
            for i in itertools.product((-1, 0, 1), repeat=dimension):
                sgci = [sgp[j] + i[j] for j in dimensions]
                for atom_position in sg.sg[sgci[0]][sgci[1]][sgci[2]][0]:
                    squared_atom_distance = sum(
                        [(atom_position[j] - p[j]) * (atom_position[j] - p[j]) for j in dimensions]
                    )
                    min_squared_atom_distance = min(min_squared_atom_distance, squared_atom_distance)
            for i in itertools.product((-1, 0, 1), repeat=dimension):
                next = False
                sgci = [sgp[j] + i[j] for j in dimensions]
                for domain_index, domain_seed_point in zip(
                    sg.sg[sgci[0]][sgci[1]][sgci[2]][2],
                    sg.sg[sgci[0]][sgci[1]][sgci[2]][1],
                ):
                    squared_domain_seed_point_distance = sum(
                        [(domain_seed_point[j] - p[j]) * (domain_seed_point[j] - p[j]) for j in dimensions]
                    )
                    if squared_domain_seed_point_distance < min_squared_atom_distance:
                        grid[p] = -domain_index - 1
                        next = True
                        break
                if next:
                    break
    return grid


def cavity_triangles(cavity_grid, cavity_indices, isolevel, step, offset, discretization_grid):
    grid = np.zeros(cavity_grid.shape, dtype=bool)

    for cavity_index in cavity_indices:
        grid = np.logical_or(grid, cavity_grid == -(cavity_index + 1))
    views = []
    for x, y, z in itertools.product(*map(range, (3, 3, 3))):
        view = grid[
            x : grid.shape[0] - 2 + x,
            y : grid.shape[1] - 2 + y,
            z : grid.shape[2] - 2 + z,
        ]
        views.append(view)
    grid = np.zeros(grid.shape, np.uint16)
    grid[:, :, :] = 0
    grid[1:-1, 1:-1, 1:-1] = sum(views) + 100

    vertices, normals = triangulate(grid, (1, 1, 1), (0, 0, 0), 100 + isolevel)
    discrete_vertices = np.array(np.floor(vertices + 0.5), dtype=np.int32)
    vertices *= np.tile(step, (vertices.shape[0], 3, 1))
    vertices += np.tile(offset, (vertices.shape[0], 3, 1))
    normals /= np.tile(step, (normals.shape[0], 3, 1))

    cavity_surface_area = 0
    for cavity_triangle, discrete_triangle in zip(vertices, discrete_vertices):
        any_outside = False
        for vertex, discrete_vertex in zip(cavity_triangle, discrete_triangle):
            if discretization_grid[tuple(discrete_vertex)] != 0:
                any_outside = True
                break
        if not any_outside:
            v1, v2, v3 = cavity_triangle
            a = v2 - v1
            b = v3 - v1
            triangle_surface_area = np.linalg.norm(np.cross(a, b)) * 0.5
            cavity_surface_area += triangle_surface_area

    return vertices, normals, cavity_surface_area


def cavity_intersections(grid, num_domains):
    intersection_table = np.zeros((num_domains, num_domains), dtype=np.int8)
    directions = []
    for dx, dy, dz in itertools.product((0, 1), repeat=3):
        if any((dx > 0, dy > 0, dz > 0)):
            directions.append((dx, dy, dz))
    for p in itertools.product(*[range(x - 1) for x in grid.shape]):
        domain1 = -grid[p] - 1
        if domain1 != -1:
            for direction in directions:
                p2 = tuple([p[i] + direction[i] for i in dimensions])
                domain2 = -grid[p2] - 1
                if domain2 != -1:
                    intersection_table[domain1][domain2] = 1
                    intersection_table[domain2][domain1] = 1
    return intersection_table


def mark_translation_vectors(grid, translation_vectors):
    # step 5
    for p in itertools.product(*map(range, grid.shape)):
        equivalent_points = [[p[i] + v[i] for i in dimensions] for v in translation_vectors]
        valid_equivalent_points = [
            tuple(point) for point in equivalent_points if all([0 <= point[i] <= grid.shape[i] - 1 for i in dimensions])
        ]
        if grid[p] == 0:
            equivalent_points_inside = [point for point in valid_equivalent_points if grid[point] == 0]
            for point in equivalent_points_inside:
                grid[point] = 1
    # step 6 & 7
    for p in itertools.product(*map(range, grid.shape)):
        equivalent_points = [([p[i] + v[i] for i in dimensions], vi) for vi, v in enumerate(translation_vectors)]
        valid_equivalent_points = [
            (tuple(point), vi)
            for point, vi in equivalent_points
            if all([0 <= point[i] <= grid.shape[i] - 1 for i in dimensions])
        ]
        if grid[p] == 1:
            equivalent_points_inside = [(point, vi) for point, vi in valid_equivalent_points if grid[point] == 0]
            if not equivalent_points_inside:
                nearest_to_center = p
                nearest_to_center_index = -1  # -1 -> -(-1+1) == 0
                min_d_center = sum([(p[i] - grid.shape[i] / 2) * (p[i] - grid.shape[i] / 2) for i in dimensions])
                for p2, vi in valid_equivalent_points:
                    d_center = sum([(p2[i] - grid.shape[i] / 2) * (p2[i] - grid.shape[i] / 2) for i in dimensions])
                    if d_center < min_d_center:
                        min_d_center = d_center
                        nearest_to_center = p2
                        nearest_to_center_index = vi
                grid[nearest_to_center] = 0
                grid[p] = -(nearest_to_center_index + 1)
            else:
                translation_vector_index = equivalent_points_inside[0][1]
                grid[p] = -(translation_vector_index + 1)
