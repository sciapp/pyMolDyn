#ifndef MARCHING_CUBES_H
#define MARCHING_CUBES_H

typedef struct {
  int *values; /* the int grid */
  int dims[3]; /* the grid dimensions */
  float size[3]; /* the grid size in world space */
  float position[3]; /* the grid position in world space */
} grid_t;

/* grid_to_triangles()
 * creates an isosurface of the volume data in grid with the given isolevel. 
 * It returns the number of triangles and sets *out_vertices and *out_normals to
 * newly allocated memory filled with the triangle vertices and the vertex normals.
 * Normals are gradient-based smooth normals, not "facette"-like per-face-normals.
 * Depending on given OpenMP support and MD_BASE_USE_OMP, the underlying 
 * "marching cubes" algorithm is parallized on the CPU.
 */
int grid_to_triangles(grid_t grid, int isolevel, float **out_vertices, float **out_normals);

/* vertices_volume()
 * returns the volume of a list of triangle mesh vertices by using the
 * signed tetrahedron volume approach.
 */
float vertices_volume(float *vertices, int num_triangles);

/* vertices_surface_area()
 * returns the surface area of a list of triangle mesh vertices by calculating
 * each triangle's surface area.
 */
float vertices_surface_area(float *vertices, int num_triangles);

#endif
