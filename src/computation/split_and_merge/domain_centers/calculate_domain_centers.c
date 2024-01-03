#include <python.h>
#include <limits.h>


typedef struct {
	int x, y, z;
} point_t;


static pyobject *calculate_domain_centers(pyobject *self, pyobject *args) {
    pyobject *atoms, *atom;
    point_t *atom_pos;
    pyobject *combined_translation_vectors, *combined_translation_vector;
    point_t *combined_trans_vecs;
    pyobject *domains, *domain_nodes, *node;
    point_t node_pos, node_dim;

    pyobject *atoms_it;
    pyobject *combined_translation_vectors_it;
    pyobject *domains_it, *domain_nodes_it;

    int i, j;
    int x, y, z;
    int combined_trans_vecs_count, atom_count;
    int min_distance, max_distance, current_distance;
    point_t diff;

    point_t current_center;

    pyobject *centers_list;

    if (!pyarg_parsetuple(args, "ooo", &atoms, &combined_translation_vectors, &domains))
    return null;

    atom_count = pylist_size(atoms);
    atom_pos = malloc(atom_count * sizeof(point_t));
    atoms_it = pyobject_getiter(atoms);
    i = 0;
    while((atom = pyiter_next(atoms_it))) {
        pyarg_parse(atom, "(iii)", &atom_pos[i].x, &atom_pos[i].y, &atom_pos[i].z);
        ++i;
        py_decref(atom);
    }
    py_decref(atoms_it);

    combined_trans_vecs_count = pysequence_size(combined_translation_vectors) + 1;
    combined_trans_vecs = malloc(combined_trans_vecs_count * sizeof(point_t));
    combined_trans_vecs[0].x = 0;
    combined_trans_vecs[0].y = 0;
    combined_trans_vecs[0].z = 0;
    combined_translation_vectors_it = pyobject_getiter(combined_translation_vectors);
    i = 1;
    while((combined_translation_vector = pyiter_next(combined_translation_vectors_it))) {
        pyarg_parse(combined_translation_vector, "(iii)", &combined_trans_vecs[i].x, &combined_trans_vecs[i].y, &combined_trans_vecs[i].z);
        ++i;
        py_decref(combined_translation_vector);
    }
    py_decref(combined_translation_vectors_it);

    centers_list = pylist_new(0);

    domains_it = pyobject_getiter(domains);
    while((domain_nodes = pyiter_next(domains_it))) {
        max_distance = -1;
        domain_nodes_it = pyobject_getiter(domain_nodes);
        while((node = pyiter_next(domain_nodes_it))) {
            pyarg_parse(node, "((iii)(iii))", &node_pos.x, &node_pos.y, &node_pos.z, &node_dim.x, &node_dim.y, &node_dim.z);
            for(x = node_pos.x; x < node_pos.x+node_dim.x; ++x) {
                for(y = node_pos.y; y < node_pos.y+node_dim.y; ++y) {
                    for(z = node_pos.z; z < node_pos.z+node_dim.z; ++z) {
                        min_distance = int_max;
                        for(i = 0; i < atom_count; ++i) {
                            for(j = 0; j < combined_trans_vecs_count; ++j) {
                                diff.x = (x-atom_pos[i].x+combined_trans_vecs[j].x);
                                diff.y = (y-atom_pos[i].y+combined_trans_vecs[j].y);
                                diff.z = (z-atom_pos[i].z+combined_trans_vecs[j].z);
                                current_distance = diff.x*diff.x + diff.y*diff.y + diff.z*diff.z;
                                if(current_distance < min_distance) {
                                    min_distance = current_distance;
                                }
                            }
                        }
                        if(min_distance > max_distance) {
                            max_distance = min_distance;
                            current_center.x = x;
                            current_center.y = y;
                            current_center.z = z;
                        }
                    }
                }
            }
            py_decref(node);
        }
        py_decref(domain_nodes_it);
        py_decref(domain_nodes);
        pylist_append(centers_list, py_buildvalue("(iii)", current_center.x, current_center.y, current_center.z));
    }
    py_decref(domains_it);

    free(atom_pos);
    free(combined_trans_vecs);

    return centers_list;
}

static pymethoddef calculate_domain_centersmethods[] = {
    {"calculate_domain_centers", calculate_domain_centers, meth_varargs, "calculates domain center points"},
    {null, null, 0, null}        /* end marker */
};

pymodinit_func
initcalculate_domain_centers(void)
{
    (void) py_initmodule("calculate_domain_centers", calculate_domain_centersmethods);
}

