# coding: utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import math
import numpy as np
import numpy.linalg as la


def calculate_gyration_tensor_parameters(points):
    """
    Calculates the gyration tensor parameters R_g^2, η, c, κ from a list of
    all points inside a cavity.
     - R_g^2 is the squared gyration radius
     - η is the asphericity
     - c is the acylindricity
     - κ is the anisotropy
    """

    points = np.array(points, dtype=np.float64)
    mean = np.mean(points, axis=0)
    points -= mean

    gyration_tensor = np.zeros((3, 3))
    for i in range(3):
        for j in range(i, 3):
            gyration_tensor[i, j] = np.dot(points[:, i], points[:, j])
            gyration_tensor[j, i] = gyration_tensor[i, j]
    # cell volume is constant, cavity volume is proportional to len(points)
    gyration_tensor /= len(points)

    eigvals = list(sorted(la.eigvalsh(gyration_tensor), reverse=True))

    squared_gyration_radius = sum(eigvals)
    if squared_gyration_radius > 0:
        asphericity = (eigvals[0] - 0.5 * (eigvals[1] + eigvals[2])) / squared_gyration_radius
        acylindricity = (eigvals[1]-eigvals[2]) / squared_gyration_radius
        anisotropy = (asphericity**2 + 0.75 * acylindricity**2)**0.5
    else:
        asphericity = 0
        acylindricity = 0
        anisotropy = 0
    return mean, squared_gyration_radius, asphericity, acylindricity, anisotropy


# Test code:


def generate_box_points(offset, side_length, n):
    return generate_cuboid_points(offset, (side_length, side_length, side_length), n)


def generate_cuboid_points(offset, side_lengths, n):
    offset = np.array(offset)
    interval = 0.5 * max(side_lengths) * np.linspace(-1, 1, n)
    points = []
    for x in interval:
        if abs(x) > 0.5 * side_lengths[0]:
            continue
        for y in interval:
            if abs(y) > 0.5 * side_lengths[1]:
                continue
            for z in interval:
                if abs(z) > 0.5 * side_lengths[2]:
                    continue
                points.append((x, y, z) + offset)
    return points


def generate_sphere_points(offset, radius, n):
    offset = np.array(offset)
    interval = radius * np.linspace(-1, 1, n)
    points = []
    for x in interval:
        for y in interval:
            for z in interval:
                if la.norm((x, y, z)) <= radius:
                    points.append((x, y, z) + offset)
    return points


def generate_cylinder_points(offset, radius, length, n):
    offset = np.array(offset)
    interval = max(radius, length/2) * np.linspace(-1, 1, n)
    points = []
    for x in interval:
        for y in interval:
            for z in interval:
                if abs(z) < length/2 and la.norm((x, y)) <= radius:
                    points.append((x, y, z) + offset)
    return points


def main():
    silly_offset = (-2, 17.3, 42)
    print('box      (a=1):            ', calculate_gyration_tensor_parameters(generate_box_points(silly_offset, 1, 100)))
    print('box      (a=2):            ', calculate_gyration_tensor_parameters(generate_box_points(silly_offset, 2, 100)))
    print('cuboid   (a=1, b=2, c=1):  ', calculate_gyration_tensor_parameters(generate_cuboid_points(silly_offset, (1, 2, 1), 100)))
    print('cuboid   (a=1, b=20, c=1): ', calculate_gyration_tensor_parameters(generate_cuboid_points(silly_offset, (1, 20, 1), 100)))
    print('sphere   (r=1):            ', calculate_gyration_tensor_parameters(generate_sphere_points(silly_offset, 1, 100)))
    print('sphere   (r=2):            ', calculate_gyration_tensor_parameters(generate_sphere_points(silly_offset, 2, 100)))
    print('cylinder (r=1, l=1):       ', calculate_gyration_tensor_parameters(generate_cylinder_points(silly_offset, 1, 1, 100)))
    print('cylinder (r=1, l=20):      ', calculate_gyration_tensor_parameters(generate_cylinder_points(silly_offset, 1, 20, 100)))


if __name__ == '__main__':
    main()
