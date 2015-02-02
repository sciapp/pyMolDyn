# -*- coding: utf-8 -*-


__all__ = ["atomstogrid"]


import numpy as np
import itertools
import sys
from math import ceil


dimension = 3
dimensions = range(dimension)


def atomstogrid(grid, discrete_positions, radii_indices, discrete_radii, translation_vectors, discretization_grid):
    last_radius_index = -1  # (for reuse of sphere grids)
    atom_information = itertools.izip(range(len(discrete_positions)),
                                      radii_indices,
                                      discrete_positions)
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
                                this_squared_distance = sum([(x - y)**2 for x, y in zip(discrete_position, p)])
                                other_position = discrete_positions[grid_value - 1]
                                for v2 in translation_vectors:
                                    other_discrete_position = [other_position[i] + v2[i] for i in dimensions]
                                    other_squared_distance = sum([(x - y)**2 for x, y in zip(other_discrete_position, p)])
                                    if other_squared_distance <= this_squared_distance:
                                        break
                                if this_squared_distance < other_squared_distance:
                                    grid[tuple(p)] = atom_index + 1


class Subgrid(object):
    def __init__(self, cubesize, grid_dimensions):
        self.cubesize = cubesize
        self.sgd = tuple(
            [2 + int(ceil(1.0 * d / cubesize)) + 2 for d in grid_dimensions])
        self.sg = []
        for x in range(self.sgd[0]):
            self.sg.append([])
            for y in range(self.sgd[1]):
                self.sg[x].append([])
                for z in range(self.sgd[2]):
                    self.sg[x][y].append([[], [], []])

    def add_atoms(self, atom_positions, translation_vectors):
        for atom_index, atom_position in enumerate(atom_positions):
            for v in translation_vectors:
                real_atom_position = [atom_position[i] + v[i] for i in dimensions]
                sgp = self.to_subgrid(real_atom_position)
                (v[0], v[1], v[2],
                real_atom_position[0],real_atom_position[1],real_atom_position[2],
                (sgp[0] * self.sgd[1] + sgp[1]) * self.sgd[1] + sgp[2])
                self.sg[sgp[0]][sgp[1]][sgp[2]][0].append(real_atom_position)

    def add_domains(self, domain_point_list, translation_vectors):
        for domain_index, domain_seed_points in enumerate(domain_point_list):
            for domain_seed_point in domain_seed_points:
                for v in translation_vectors:
                    real_domain_seed_point = [domain_seed_point[i] + v[i] for i in dimensions]
                    sgp = self.to_subgrid(real_domain_seed_point)
                    (v[0], v[1], v[2],
                    real_domain_seed_point[0],real_domain_seed_point[1],real_domain_seed_point[2],
                    (sgp[0] * self.sgd[1] + sgp[1]) * self.sgd[1] + sgp[2])
                    self.sg[sgp[0]][sgp[1]][sgp[2]][1].append(real_domain_seed_point)
                    self.sg[sgp[0]][sgp[1]][sgp[2]][2].append(domain_index)

    def to_subgrid(self, position):
        sgp = [c / self.cubesize + 2 for c in position]
        for i in dimensions:
            if sgp[i] < 0:
                sgp[i] = 0
            if sgp[i] >= self.sgd[i]:
                sgp[i] = self.sgd[i] - 1
        return tuple(sgp)


def mark_cavities(domain_grid,
        discretization_grid,
        grid_dimensions,
        sg_cube_size,
        atom_positions,
        translation_vectors,
        domain_point_list,
        use_surface_points):

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
                possibly_in_cavity = False # is already marked
            elif grid_value > 0:  # in radius of atom (stored as: index+1), therefore possibly in a cavity
                grid[p] = 0
                possibly_in_cavity = True
        else:
            possibly_in_cavity = (discretization_grid[p] == 0)
        if possibly_in_cavity:
            # step 5
            min_squared_atom_distance = sys.maxint
            sgp = sg.to_subgrid(p)
            for i in itertools.product((-1, 0, 1), repeat=dimension):
                sgci = [sgp[j] + i[j] for j in dimensions]
                for atom_position in sg.sg[sgci[0]][sgci[1]][sgci[2]][0]:
                    squared_atom_distance = sum(
                        [(atom_position[j] - p[j]) * (atom_position[j] - p[j]) for j in dimensions])
                    min_squared_atom_distance = min(min_squared_atom_distance, squared_atom_distance)
            for i in itertools.product((-1, 0, 1), repeat=dimension):
                next = False
                sgci = [sgp[j] + i[j] for j in dimensions]
                for domain_index, domain_seed_point in zip(sg.sg[sgci[0]][sgci[1]][sgci[2]][2],
                                                           sg.sg[sgci[0]][sgci[1]][sgci[2]][1]):
                    squared_domain_seed_point_distance = sum(
                        [(domain_seed_point[j] - p[j]) * (domain_seed_point[j] - p[j]) for j in dimensions])
                    if squared_domain_seed_point_distance < min_squared_atom_distance:
                        grid[p] = -domain_index - 1
                        next = True
                        break
                if next:
                    break
    return grid

