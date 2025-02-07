#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <numpy/ndarraytypes.h>


#define IS_EQUIVALENT(a, b) ((!(a) || (b)) && (!(b) || (a)))

typedef struct {
    int x, y, z;
} point_t;


static PyObject *find_index_of_first_element_not_equivalent(PyObject *self, PyObject *args) {
    int x, y, z;
    int done = 0;
    point_t pos = {-1, -1, -1};

    PyArrayObject *array;
    PyArrayObject *mask_array;
    int elem, current_elem;
    char mask_elem, current_mask_elem;
    int *data;
    char *mask;
    npy_intp *shape;
    npy_intp *data_stride, *mask_stride;

    if (!PyArg_ParseTuple(args, "OO", &array, &mask_array))
    return NULL;

    data   = (int *)  PyArray_BYTES(array);
    mask   = (char *) PyArray_BYTES(mask_array);
    shape  = PyArray_DIMS(array);
    data_stride = PyArray_STRIDES(array);
    mask_stride = PyArray_STRIDES(mask_array);

    elem = *data;
    mask_elem = *mask;
    for(x = 0; x < shape[0]; ++x) {
        for(y = 0; y < shape[1]; ++y) {
            for(z = 0; z < shape[2]; ++z) {
                current_elem = data[
                    x*data_stride[0]/sizeof(int) +
                    y*data_stride[1]/sizeof(int) +
                    z*data_stride[2]/sizeof(int)
                ];
                current_mask_elem = mask[x*mask_stride[0] + y*mask_stride[1] + z*mask_stride[2]];
                if(!IS_EQUIVALENT(current_elem, elem) || !IS_EQUIVALENT(current_mask_elem, mask_elem)) {
                    pos.x = x;
                    pos.y = y;
                    pos.z = z;
                    done = 1;
                    break;
                }
            }
            if(done) break;
        }
        if(done) break;
    }

    return Py_BuildValue("(iii)", pos.x, pos.y, pos.z);
}

static PyMethodDef FindMethods[] = {
    {
        "find_index_of_first_element_not_equivalent",
        find_index_of_first_element_not_equivalent,
        METH_VARARGS,
        "Finds the first index in a numpy array that is unequal to a given value"
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef findmodule = {
    PyModuleDef_HEAD_INIT,
    "find_index_of_first_element_not_equivalent",  /* name of module */
    NULL,                                          /* module documentation */
    -1,                                            /* size of per-interpreter state of the module */
    FindMethods
};

PyMODINIT_FUNC
PyInit_find_index_of_first_element_not_equivalent(void) {
    return PyModule_Create(&findmodule);
}
