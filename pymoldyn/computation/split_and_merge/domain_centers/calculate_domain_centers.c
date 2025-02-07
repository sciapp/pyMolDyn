#include <Python.h>
#include <limits.h>

typedef struct {
    int x, y, z;
} point_t;

static PyObject *calculate_domain_centers(PyObject *self, PyObject *args) {
    PyObject *atoms, *atom;
    point_t *atom_pos;
    PyObject *combined_translation_vectors, *combined_translation_vector;
    point_t *combined_trans_vecs;
    PyObject *domains, *domain_nodes, *node;
    point_t node_pos, node_dim;

    PyObject *atoms_it;
    PyObject *combined_translation_vectors_it;
    PyObject *domains_it, *domain_nodes_it;

    int i, j;
    int x, y, z;
    int combined_trans_vecs_count, atom_count;
    int min_distance, max_distance, current_distance;
    point_t diff;

    point_t current_center;

    PyObject *centers_list;

    // Parse Python arguments (expecting three lists)
    if (!PyArg_ParseTuple(args, "OOO", &atoms, &combined_translation_vectors, &domains)) {
        return NULL;
    }

    // Ensure atoms is a list
    if (!PyList_Check(atoms)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a list");
        return NULL;
    }

    atom_count = PyList_Size(atoms);
    atom_pos = malloc(atom_count * sizeof(point_t));

    // Iterate over atoms list and parse (x, y, z) for each atom
    atoms_it = PyObject_GetIter(atoms);
    i = 0;
    while((atom = PyIter_Next(atoms_it))) {
        if (!PyArg_ParseTuple(atom, "iii", &atom_pos[i].x, &atom_pos[i].y, &atom_pos[i].z)) {
            Py_DECREF(atom);
            Py_DECREF(atoms_it);
            free(atom_pos);
            PyErr_SetString(PyExc_TypeError, "Invalid atom format, expected (x, y, z)");
            return NULL;
        }
        ++i;
        Py_DECREF(atom);
    }
    Py_DECREF(atoms_it);

    // Handle combined_translation_vectors
    combined_trans_vecs_count = PySequence_Size(combined_translation_vectors) + 1;
    combined_trans_vecs = malloc(combined_trans_vecs_count * sizeof(point_t));
    combined_trans_vecs[0].x = 0;
    combined_trans_vecs[0].y = 0;
    combined_trans_vecs[0].z = 0;

    combined_translation_vectors_it = PyObject_GetIter(combined_translation_vectors);
    i = 1;
    while((combined_translation_vector = PyIter_Next(combined_translation_vectors_it))) {
        if (
            !PyArg_ParseTuple(
                combined_translation_vector,
                "iii",
                &combined_trans_vecs[i].x,
                &combined_trans_vecs[i].y,
                &combined_trans_vecs[i].z
            )
        ) {
            Py_DECREF(combined_translation_vector);
            Py_DECREF(combined_translation_vectors_it);
            free(atom_pos);
            free(combined_trans_vecs);
            PyErr_SetString(PyExc_TypeError, "Invalid translation vector format, expected (x, y, z)");
            return NULL;
        }
        ++i;
        Py_DECREF(combined_translation_vector);
    }
    Py_DECREF(combined_translation_vectors_it);

    // Prepare centers list
    centers_list = PyList_New(0);

    // Iterate over domains and calculate centers
    domains_it = PyObject_GetIter(domains);
    while((domain_nodes = PyIter_Next(domains_it))) {
        max_distance = -1;
        domain_nodes_it = PyObject_GetIter(domain_nodes);
        while((node = PyIter_Next(domain_nodes_it))) {
            PyObject *pos_tuple, *dim_tuple;
            pos_tuple = PyTuple_GetItem(node, 0);
            dim_tuple = PyTuple_GetItem(node, 1);
            if (!PyArg_ParseTuple(pos_tuple, "iii", &node_pos.x, &node_pos.y, &node_pos.z)) {
                Py_DECREF(node);
                Py_DECREF(domain_nodes_it);
                Py_DECREF(domain_nodes);
                Py_DECREF(domains_it);
                free(atom_pos);
                free(combined_trans_vecs);
                return NULL;
            }
            if (!PyArg_ParseTuple(dim_tuple, "iii", &node_dim.x, &node_dim.y, &node_dim.z)) {
                Py_DECREF(node);
                Py_DECREF(domain_nodes_it);
                Py_DECREF(domain_nodes);
                Py_DECREF(domains_it);
                free(atom_pos);
                free(combined_trans_vecs);
                return NULL;
            }

            for (x = node_pos.x; x < node_pos.x + node_dim.x; ++x) {
                for (y = node_pos.y; y < node_pos.y + node_dim.y; ++y) {
                    for (z = node_pos.z; z < node_pos.z + node_dim.z; ++z) {
                        min_distance = INT_MAX;
                        for (i = 0; i < atom_count; ++i) {
                            for (j = 0; j < combined_trans_vecs_count; ++j) {
                                diff.x = (x - atom_pos[i].x + combined_trans_vecs[j].x);
                                diff.y = (y - atom_pos[i].y + combined_trans_vecs[j].y);
                                diff.z = (z - atom_pos[i].z + combined_trans_vecs[j].z);
                                current_distance = diff.x * diff.x + diff.y * diff.y + diff.z * diff.z;
                                if (current_distance < min_distance) {
                                    min_distance = current_distance;
                                }
                            }
                        }
                        if (min_distance > max_distance) {
                            max_distance = min_distance;
                            current_center.x = x;
                            current_center.y = y;
                            current_center.z = z;
                        }
                    }
                }
            }
            Py_DECREF(node);
        }
        Py_DECREF(domain_nodes_it);
        Py_DECREF(domain_nodes);

        // Append the current center to centers_list
        PyList_Append(centers_list, Py_BuildValue("(iii)", current_center.x, current_center.y, current_center.z));
    }
    Py_DECREF(domains_it);

    free(atom_pos);
    free(combined_trans_vecs);

    return centers_list;
}

// Method definition object
static PyMethodDef FindMethods[] = {
    {"calculate_domain_centers", calculate_domain_centers, METH_VARARGS, "calculates domain center points"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

// Module definition
static struct PyModuleDef findmodule = {
    PyModuleDef_HEAD_INIT,
    "calculate_domain_centers",
    NULL,
    -1,
    FindMethods
};

// Module initialization function
PyMODINIT_FUNC
PyInit_calculate_domain_centers(void) {
    return PyModule_Create(&findmodule);
}
