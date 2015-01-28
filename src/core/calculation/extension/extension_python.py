# -*- coding: utf-8 -*-


__all__ = ["atomstogrid"]


import numpy as np
import itertools
import sys


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


def mark_cavities(domain_grid,
        discretization_grid,
        grid_dimensions,
        sg, sg_cube_size, to_subgrid,
        atom_positions,
        translation_vectors,
        surface_point_list,
        use_surface_points):
    grid = np.zeros(grid_dimensions, dtype=np.int64)
    for p in itertools.product(*map(range, grid_dimensions)):
        if use_surface_points:
            grid_value = domain_grid[p]
            if grid_value == 0:  # outside the volume
                grid[p] = 0
                possibly_in_cavity = False
            elif grid_value < 0:  # cavity domain (stored as: -index-1), therefore guaranteed to be in a cavity
                grid[p] = grid_value
                possibly_in_cavity = True
            elif grid_value > 0:  # in radius of atom (stored as: index+1), therefore possibly in a cavity
                grid[p] = 0
                possibly_in_cavity = True
        else:
            possibly_in_cavity = (discretization_grid[p] == 0)
        if possibly_in_cavity:
            # step 5
            min_squared_atom_distance = sys.maxint
            sgp = to_subgrid(p)
            for i in itertools.product((0, 1, -1), repeat=dimension):
                sgci = [sgp[j] + i[j] for j in dimensions]
                for atom_position in sg[sgci[0]][sgci[1]][sgci[2]][0]:
                    squared_atom_distance = sum(
                        [(atom_position[j] - p[j]) * (atom_position[j] - p[j]) for j in dimensions])
                    min_squared_atom_distance = min(min_squared_atom_distance, squared_atom_distance)
            for i in itertools.product((0, 1, -1), repeat=dimension):
                next = False
                sgci = [sgp[j] + i[j] for j in dimensions]
                for domain_index, domain_seed_point in zip(sg[sgci[0]][sgci[1]][sgci[2]][2],
                                                           sg[sgci[0]][sgci[1]][sgci[2]][1]):
                    squared_domain_seed_point_distance = sum(
                        [(domain_seed_point[j] - p[j]) * (domain_seed_point[j] - p[j]) for j in dimensions])
                    if squared_domain_seed_point_distance < min_squared_atom_distance:
                        grid[p] = -domain_index - 1
                        next = True
                        break
                if next:
                    break
    return grid

