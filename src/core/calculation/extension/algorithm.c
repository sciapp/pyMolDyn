#include <stdlib.h>

#define SQUARE(x) ((x)*(x))
#define INDEXCUBE(i,j,k) (((i)*cubesize+(j))*cubesize+(k))
#define INDEXGRID(i,j,k) ((int64_t)(i)*strides[0]+(j)*strides[1]+(k)*strides[2])
#define INDEXDISCGRID(i,j,k) ((int64_t)(i)*discgrid_strides[0]+(j)*discgrid_strides[1]+(k)*discgrid_strides[2])

/**
 * Mark spheres around atoms on the grid.
 * For each discretized atom and its equivalents in adjacent cells:
 * for each cell of the discretized sphere around them:
 * find the grid cells which are inside the cutoff radius.
 * For each of this grid cells:
 * check if the cell is inside the volume,
 * check if this atom is the closest to this cell
 * and write the atom index (+1) into it.
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
    int grid_index;
    int grid_value;
    int this_squared_distance;
    int other_squared_distance;
    int other_atompos[3];
    int other_transpos[3];

    (void) nradii;

    for (i = 0; i < natoms; i++) {
        radius = radii[radii_indices[i]];
        cubesize = 2 * radius + 1;
        atompos[0] = atom_positions[i * 3 + 0];
        atompos[1] = atom_positions[i * 3 + 1];
        atompos[2] = atom_positions[i * 3 + 2];
        for (j = 0; j < ntranslations; j++) {
            transpos[0] = atompos[0] + translations[j * 3 + 0];
            transpos[1] = atompos[1] + translations[j * 3 + 1];
            transpos[2] = atompos[2] + translations[j * 3 + 2];
            if (transpos[0] + radius < 0 || transpos[0] - radius >= dimensions[0]
                    || transpos[1] + radius < 0 || transpos[1] - radius >= dimensions[1]
                    || transpos[2] + radius < 0 || transpos[2] - radius >= dimensions[2]) {
                /* entire cube is outside */
                continue;
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
                            grid_index = INDEXGRID(gridpos[0], gridpos[1], gridpos[2]);
                            grid_value = grid[grid_index];
                            /* check if it is the closest atom */
                            if (grid_value == 0) {
                                grid[grid_index] = i + 1;
                            } else {
                                this_squared_distance = SQUARE(transpos[0] - gridpos[0])
                                        + SQUARE(transpos[1] - gridpos[1])
                                        + SQUARE(transpos[2] - gridpos[2]);
                                other_atompos[0] = atom_positions[3 * (grid_value - 1) + 0];
                                other_atompos[1] = atom_positions[3 * (grid_value - 1) + 1];
                                other_atompos[2] = atom_positions[3 * (grid_value - 1) + 2];
                                for (k = 0; k < ntranslations; k++) {
                                    other_transpos[0] = other_atompos[0] + translations[k * 3 + 0];
                                    other_transpos[1] = other_atompos[1] + translations[k * 3 + 1];
                                    other_transpos[2] = other_atompos[2] + translations[k * 3 + 2];
                                    other_squared_distance = SQUARE(other_transpos[0] - gridpos[0])
                                            + SQUARE(other_transpos[1] - gridpos[1])
                                            + SQUARE(other_transpos[2] - gridpos[2]);
                                    if (other_squared_distance <= this_squared_distance) {
                                        break;
                                    }
                                }
                                if (this_squared_distance < other_squared_distance) {
                                    grid[grid_index] = i + 1;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
