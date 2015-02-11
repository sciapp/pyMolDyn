#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <gr3.h>

#define SQUARE(x) ((x)*(x))
#define CLIP(x,a,b) ((x)<(a)?(a):((x)>(b)?(b):(x)))


typedef struct subgrid_cell {
    int num_atoms;
    int *atom_positions;
    int num_domains;
    int *domain_points;
    int *domain_indices;
} subgrid_cell_t;

typedef struct subgrid {
    subgrid_cell_t *a;
    int cubesize;
    int ncells;
    int dimensions[3];
    int strides[3];
} subgrid_t;


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

#undef INDEXGRID
#undef INDEXDISCGRID


/**
 * Routines to work with subgrids
 */

subgrid_t *subgrid_create(int cubesize, int grid_dimensions[3])
{
    subgrid_t *sg;
    int k;

    sg = malloc(sizeof(subgrid_t));
    sg->cubesize = cubesize;
    for (k = 0; k < 3; k++) {
        sg->dimensions[k] = (int) ceil((double) grid_dimensions[k] / cubesize) + 4;
    }
    sg->ncells = sg->dimensions[0] * sg->dimensions[1] * sg->dimensions[2];
    sg->strides[0] = sg->dimensions[1] * sg->dimensions[2];
    sg->strides[1] = sg->dimensions[2];
    sg->strides[2] = 1;

    sg->a = calloc(sg->ncells, sizeof(subgrid_cell_t));

    return sg;
}

void subgrid_destroy(subgrid_t *sg)
{
    int i;

    for (i = 0; i < sg->ncells; i++) {
        free(sg->a[i].atom_positions);
        free(sg->a[i].domain_points);
        free(sg->a[i].domain_indices);
    }
    free(sg->a);
    free(sg);
}

static
int subgrid_index(subgrid_t *sg, int *pos)
{
    int k;
    int z;
    int index;

    index = 0;
    for (k = 0; k < 3; k++) {
        /* python's floor division */
        z = (int) (floor((double) pos[k] / sg->cubesize)) + 2;
        index += CLIP(z, 0, sg->dimensions[k] - 1) * sg->strides[k];
    }
    return index;
}

void subgrid_add_atoms(subgrid_t *sg,
        int natoms, int *atom_positions,
        int ntranslations, int *translations)
{
    int i, j;
    int real_pos[3];
    subgrid_cell_t *cell;

    for (i = 0; i < natoms; i++) {
        for (j = 0; j < ntranslations; j++) {
            real_pos[0] = atom_positions[i * 3 + 0] + translations[j * 3 + 0];
            real_pos[1] = atom_positions[i * 3 + 1] + translations[j * 3 + 1];
            real_pos[2] = atom_positions[i * 3 + 2] + translations[j * 3 + 2];
            cell = sg->a + subgrid_index(sg, real_pos);
            cell->atom_positions = realloc(cell->atom_positions,
                    (cell->num_atoms + 1) * 3 * sizeof(int));
            cell->atom_positions[3 * cell->num_atoms + 0] = real_pos[0];
            cell->atom_positions[3 * cell->num_atoms + 1] = real_pos[1];
            cell->atom_positions[3 * cell->num_atoms + 2] = real_pos[2];
            cell->num_atoms++;
        }
    }
}

void subgrid_add_domains(subgrid_t *sg,
        int npoints, int *domain_indices, int *domain_points,
        int ntranslations, int *translations)
{
    int i, j;
    int real_pos[3];
    subgrid_cell_t *cell;

    for (i = 0; i < npoints; i++) {
        for (j = 0; j < ntranslations; j++) {
            real_pos[0] = domain_points[i * 3 + 0] + translations[j * 3 + 0];
            real_pos[1] = domain_points[i * 3 + 1] + translations[j * 3 + 1];
            real_pos[2] = domain_points[i * 3 + 2] + translations[j * 3 + 2];
            cell = sg->a + subgrid_index(sg, real_pos);
            cell->domain_indices = realloc(cell->domain_indices,
                    (cell->num_domains + 1) * sizeof(int));
            cell->domain_indices[cell->num_domains] = domain_indices[i];
            cell->domain_points = realloc(cell->domain_points,
                    (cell->num_domains + 1) * 3 * sizeof(int));
            cell->domain_points[3 * cell->num_domains + 0] = real_pos[0];
            cell->domain_points[3 * cell->num_domains + 1] = real_pos[1];
            cell->domain_points[3 * cell->num_domains + 2] = real_pos[2];
            cell->num_domains++;
        }
    }
}


#define INDEXGRID(i,j,k) ((int64_t)(i)*strides[0]+(j)*strides[1]+(k)*strides[2])
#define INDEXDISCGRID(i,j,k) ((int64_t)(i)*discgrid_strides[0]+(j)*discgrid_strides[1]+(k)*discgrid_strides[2])

/**
 * For each cell, determine if it is closer to a cavity domain than
 * to an atom center. If so, mark the cell in the grid.
 */
void mark_cavities(int64_t *grid, int64_t *domain_grid, int dimensions[3], int strides[3],
        char *discretization_grid, int discgrid_strides[3],
        subgrid_t *sg, int use_surface_points)
{
    int pos[3];
    int grid_index;
    int grid_value;
    int sg_index;
    int min_squared_atom_distance;
    int squared_atom_distance;
    int neigh[3];
    int neigh_index;
    subgrid_cell_t *cell;
    int i;
    int breaknext;
    int squared_domain_distance;

    for (pos[0] = 0; pos[0] < dimensions[0]; pos[0]++) {
        for (pos[1] = 0; pos[1] < dimensions[1]; pos[1]++) {
            for (pos[2] = 0; pos[2] < dimensions[2]; pos[2]++) {
                grid_index = INDEXGRID(pos[0], pos[1], pos[2]);
                if (use_surface_points) {
                    grid_value = domain_grid[grid_index];
                    if (grid_value == 0) {
                        /* outside the volume */
                        grid[grid_index] = 0;
                        continue;
                    } else if (grid_value < 0) {
                        /* cavity domain (stored as: -index-1), therefore guaranteed to be in a cavity */
                        grid[grid_index] = grid_value;
                        continue;
                    } else {
                        grid[grid_index] = 0;
                    }
                } else {
                    if (discretization_grid[INDEXDISCGRID(pos[0], pos[1], pos[2])] != 0) {
                        continue;
                    }
                }
                /* step 5 */
                min_squared_atom_distance = INT_MAX;
                sg_index = subgrid_index(sg, pos);
                for (neigh[0] = -1; neigh[0] <= 1; neigh[0]++) {
                    for (neigh[1] = -1; neigh[1] <= 1; neigh[1]++) {
                        for (neigh[2] = -1; neigh[2] <= 1; neigh[2]++) {
                            neigh_index = sg_index + neigh[0] * sg->strides[0]
                                    + neigh[1] * sg->strides[1]
                                    + neigh[2] * sg->strides[2];
                            cell = sg->a + neigh_index;
                            for (i = 0; i < cell->num_atoms; i++) {
                                squared_atom_distance = 
                                        SQUARE(cell->atom_positions[i * 3 + 0] - pos[0])
                                        + SQUARE(cell->atom_positions[i * 3 + 1] - pos[1])
                                        + SQUARE(cell->atom_positions[i * 3 + 2] - pos[2]);
                                if (squared_atom_distance < min_squared_atom_distance) {
                                    min_squared_atom_distance = squared_atom_distance;
                                }
                            }
                        }
                    }
                }
                breaknext = 0;
                for (neigh[0] = -1; neigh[0] <= 1; neigh[0]++) {
                    for (neigh[1] = -1; neigh[1] <= 1; neigh[1]++) {
                        for (neigh[2] = -1; neigh[2] <= 1; neigh[2]++) {
                            neigh_index = sg_index + neigh[0] * sg->strides[0]
                                    + neigh[1] * sg->strides[1]
                                    + neigh[2] * sg->strides[2];
                            cell = sg->a + neigh_index;
                            for (i = 0; i < cell->num_domains; i++) {
                                squared_domain_distance = 
                                        SQUARE(cell->domain_points[i * 3 + 0] - pos[0])
                                        + SQUARE(cell->domain_points[i * 3 + 1] - pos[1])
                                        + SQUARE(cell->domain_points[i * 3 + 2] - pos[2]);
                                if (squared_domain_distance < min_squared_atom_distance) {
                                    grid[grid_index] = -cell->domain_indices[i] - 1;
                                    breaknext = 1;
                                    break; /* i */
                                }
                            }
                            if (breaknext) {
                                break; /* neigh[2] */
                            }
                        }
                        if (breaknext) {
                            break; /* neigh[1] */
                        }
                    }
                    if (breaknext) {
                        break; /* neigh[0] */
                    }
                }
            }
        }
    }
}
#undef INDEXGRID
#undef INDEXDISCGRID


#define INDEXGRID(i,j,k) ((int64_t)(i)*strides[0]+(j)*strides[1]+(k)*strides[2])
#define INDEXDISCGRID(i,j,k) ((int64_t)(i)*discgrid_strides[0]+(j)*discgrid_strides[1]+(k)*discgrid_strides[2])
int cavity_triangles(
        int64_t *cavity_grid,
        int dimensions[3],
        int strides[3],
        int ncavity_indices,
        int *cavity_indices,
        int isolevel,
        float step[3],
        float offset[3],
        int8_t *discretization_grid,
        int discgrid_strides[3],
        float **vertices,
        float **normals,
        float *surface_area)
{
    uint16_t *counts;
    int pos[3];
    int gridindex;
    int gridval;
    int i, j, k;
    int is_cavity;
    int neigh[3];
    int neighindex;
    int bbox[2][3] = {{-1, -1, -1}, {-1, -1, -1}};
    int ntriangles;
    float *triangles_p;
    float *continuous_vertices;
    float *continuous_normals;
    double area;
    int any_outside;
    float *vertex_p;
    float *normal_p;
    int disc_pos[3];
    double a[3], b[3];
    double cross[3];

    counts = calloc(dimensions[0] * dimensions[1] * dimensions[2],
            sizeof(uint16_t));
    for (pos[0] = 1; pos[0] < dimensions[0] - 1; pos[0]++) {
        for (pos[1] = 1; pos[1] < dimensions[1] - 1; pos[1]++) {
            for (pos[2] = 1; pos[2] < dimensions[2] - 1; pos[2]++) {
                gridindex = INDEXGRID(pos[0], pos[1], pos[2]);
                counts[gridindex] += 100;
                gridval = cavity_grid[gridindex];
                is_cavity = 0;
                for (i = 0; i < ncavity_indices; i++) {
                    if (gridval == -cavity_indices[i] - 1) {
                        is_cavity = 1;
                        break;
                    }
                }
                if (!is_cavity) {
                    continue;
                }
                for (neigh[0] = -1; neigh[0] <= 1; neigh[0]++) {
                    for (neigh[1] = -1; neigh[1] <= 1; neigh[1]++) {
                        for (neigh[2] = -1; neigh[2] <= 1; neigh[2]++) {
                            neighindex = gridindex + INDEXGRID(
                                    neigh[0], neigh[1], neigh[2]);
                            counts[neighindex]++;
                        }
                    }
                }
                for (i = 0; i < 3; i++) {
                    if (bbox[0][i] == -1 ||
                            bbox[0][i] > pos[i] - 1) {
                        bbox[0][i] = pos[i] - 1;
                    }
                    if (bbox[1][i] == -1 ||
                            bbox[1][i] < pos[i] + 1) {
                        bbox[1][i] = pos[i] + 1;
                    }
                }
            }
        }
    }
    for (i = 0; i < 3; i++) {
        if (bbox[0][i] >= 1) {
            bbox[0][i]--;
        }
        if (bbox[1][i] < dimensions[i] - 1) {
            bbox[1][i]++;
        }
    }
    
    ntriangles = gr3_triangulate(
            counts + INDEXGRID(bbox[0][0], bbox[0][1], bbox[0][2]),
            100 + isolevel,
            bbox[1][0] - bbox[0][0] + 1,
            bbox[1][1] - bbox[0][1] + 1,
            bbox[1][2] - bbox[0][2] + 1,
            strides[0], strides[1], strides[2],
            1.0, 1.0, 1.0,
            bbox[0][0], bbox[0][1], bbox[0][2],
            (gr3_triangle_t **) &triangles_p);
    free(counts);

    continuous_vertices = malloc(ntriangles * 3 * 3 * sizeof(float));
    continuous_normals = malloc(ntriangles * 3 * 3 * sizeof(float));
    area = 0.0;
    for (i = 0; i < ntriangles; i++) {
        any_outside = 0;
        for (j = 0; j < 3; j++) {
            vertex_p = triangles_p + (i * 3 * 2 + j) * 3;
            normal_p = vertex_p + 3 * 3;
            for (k = 0; k < 3; k++) {
                disc_pos[k] = floor(vertex_p[k] + 0.5);
                continuous_vertices[(i * 3 + j) * 3 + k] = 
                        vertex_p[k] * step[k] + offset[k];
                continuous_normals[(i * 3 + j) * 3 + k] = 
                        normal_p[k] / step[k];
            }
            if (discretization_grid[INDEXDISCGRID(
                    disc_pos[0], disc_pos[1], disc_pos[2])] != 0) {
                any_outside = 1;
            }
        }
        if (!any_outside) {
            for (k = 0; k < 3; k++) {
                a[k] = continuous_vertices[(i * 3 + 1) * 3 + k]
                        - continuous_vertices[(i * 3 + 0) * 3 + k];
                b[k] = continuous_vertices[(i * 3 + 2) * 3 + k]
                        - continuous_vertices[(i * 3 + 0) * 3 + k];
            }
            cross[0] = a[1] * b[2] - a[2] * b[1];
            cross[1] = a[2] * b[0] - a[0] * b[2];
            cross[2] = a[0] * b[1] - a[1] * b[0];
            area += 0.5 * sqrt(cross[0] * cross[0]
                    + cross[1] * cross[1] + cross[2] * cross[2]);
        }
    }
    free(triangles_p);

    *vertices = continuous_vertices;
    *normals = continuous_normals;
    *surface_area = area;
    return ntriangles;
}
#undef INDEXGRID
#undef INDEXDISCGRID


void free_float_p(float *p)
{
    free(p);
}
