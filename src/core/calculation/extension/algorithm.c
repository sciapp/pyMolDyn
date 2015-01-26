#include <stdlib.h>

#define SQUARE(x) ((x)*(x))
#define INDEXCUBE(i,j,k) (((i)*cubesize+(j))*cubesize+(k))
#define INDEXGRID(i,j,k) ((int64_t)(i)*strides[0]+(j)*strides[1]+(k)*strides[2])
#define INDEXDISCGRID(i,j,k) ((int64_t)(i)*discgrid_strides[0]+(j)*discgrid_strides[1]+(k)*discgrid_strides[2])

/**
 * Mark spheres around atoms on the grid.
 * For each discretized atom and its equivalents in adjacent cells,
 * for each cell of the discretized sphere around them,
 * find the grid cells in which it lies,
 * and write the atom index into it, if the value is 0.
 */
void atomstogrid(
        int64_t *grid, int dimensions[3], int strides[3],
        int natoms, int *atom_positions, int *radii_indices,
        int nradii, int *radii,
        int ntranslations, int *translations,
        char *discretization_grid, int discgrid_strides[3])
{
    int i, j, k;
    int radius;
    int cubesize;
    int atompos[3];
    int transpos[3];
    int sphereindex[3];
    int gridpos[3];

    (void) nradii;

    for (i = 0; i < natoms; i++) {
        radius = radii[radii_indices[i]];
        cubesize = 2 * radius + 1;
        for (k = 0; k < 3; k++) {
            atompos[k] = atom_positions[i * 3 + k];
        }
        for (j = 0; j < ntranslations; j++) {
            for (k = 0; k < 3; k++) {
                transpos[k] = atompos[k] + translations[j * 3 + k];
            }
            for (sphereindex[0] = 0; sphereindex[0] < cubesize; sphereindex[0]++) {
                gridpos[0] = transpos[0] + sphereindex[0] - radius;
                if (gridpos[0] < 0 || gridpos[0] >= dimensions[0]) {
                    continue;
                }
                for (sphereindex[1] = 0; sphereindex[1] < cubesize; sphereindex[1]++) {
                    gridpos[1] = transpos[1] + sphereindex[1] - radius;
                    if (gridpos[1] < 0 || gridpos[1] >= dimensions[1]) {
                        continue;
                    }
                    for (sphereindex[2] = 0; sphereindex[2] < cubesize; sphereindex[2]++) {
                        gridpos[2] = transpos[2] + sphereindex[2] - radius;
                        if (gridpos[2] < 0 || gridpos[2] >= dimensions[2]) {
                            continue;
                        }
                        if (SQUARE(sphereindex[0] - radius)
                                + SQUARE(sphereindex[1] - radius)
                                + SQUARE(sphereindex[2] - radius)
                                <= SQUARE(radius) 
                                && discretization_grid[INDEXDISCGRID(gridpos[0], gridpos[1], gridpos[2])] == 0) {
                            grid[INDEXGRID(gridpos[0], gridpos[1], gridpos[2])] = i + 1;
                        }
                    }
                }
            }
        }
    }
}
