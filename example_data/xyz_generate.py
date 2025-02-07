from math import pi, sqrt

import numpy as np

with open("generated2.xyz", "w") as f:
    f.write("1000\n")

    width = 10.0
    depth = 10.0
    height = 10.0

    g1 = width * np.array([1, 0, 0])
    g2 = depth * np.array([1 / sqrt(2), 0, -1 / sqrt(2)])
    g3 = height * np.array([1 / sqrt(2), 1 / sqrt(sqrt(2)), 1 / sqrt(2) - 1])
    print(g1)
    print(g2)
    print(g3)
    angles = [45, 45, 45]

    #    width = 10.
    #    depth = 20.
    #    height = 30.
    #
    #    g1 = width * np.array([1,0,0])
    #    g2 = depth * np.array([0,1,0])
    #    g3 = height * np.array([0,0,1])
    #    angles = [90, 90, 90]

    f.write("TRI {0} {1} {2} {3} {4} {5}\n".format(width, depth, height, *[ang / 365.0 * 2 * pi for ang in angles]))

    bound = [0, 11]
    for a in range(bound[0], bound[1]):  # g3-cells
        for b in range(bound[0], bound[1]):  # g2-cells
            for c in range(bound[0], bound[1]):  # g1-cells
                p = c / 10.0 * g1 + b / 10.0 * g2 + a / 10.0 * g3
                f.write("Sb   {}   {}   {}\n".format(p[0], p[1], p[2]))
