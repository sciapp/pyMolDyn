from ctypes import *
import numpy as np
_mc = CDLL('libmc.so')
_mc.triangulate.restype = c_uint
_mc.triangulate.argtypes = (POINTER(c_ushort), c_int,
                            c_uint, c_uint, c_uint,
                            c_uint, c_uint, c_uint,
                            c_double, c_double, c_double,
                            c_double, c_double, c_double,
                            POINTER(POINTER(c_double)))
                            
_mc.free_triangles.restype = None
_mc.free_triangles.argtypes = (POINTER(c_double),)


def triangulate(grid, step, offset, isolevel, slices = None):
    data = grid.ctypes.data_as(POINTER(c_ushort))
    isolevel = c_int(isolevel)
    if slices is None:
        dim_x, dim_y, dim_z = map(c_uint, grid.shape)
        stride_x, stride_y, stride_z = (0, 0, 0)
    else:
        stride_x = grid.shape[2]*grid.shape[1]
        stride_y = grid.shape[2]
        stride_z = 1
        for i, slice in enumerate(slices):
            if slice[0] >= slice[1]:
                raise ValueError("first slice value must be less than the second value (axis=%d)" % i)
            if slice[0] < 0:
                raise ValueError("slice values must be positive (axis=%d)" % i)
            if slice[1] > grid.shape[i]:
                raise ValueError("second slice value must be at most as large as the grid dimension (axis=%d)" % i)
        dim_x, dim_y, dim_z = [c_uint(slice[1]-slice[0]) for slice in slices]
        data_offset = 2*(stride_x*slices[0][0] + stride_y*slices[1][0] + stride_z*slices[2][0])
        data_address = cast(byref(data), POINTER(c_ulong)).contents.value
        data_address += data_offset
        data = cast(POINTER(c_ulong)(c_ulong(data_address)), POINTER(POINTER(c_ushort))).contents
        offset = [offset[i] + slices[i][0]*step[i] for i in range(3)]
    stride_x = c_uint(stride_x)
    stride_y = c_uint(stride_y)
    stride_z = c_uint(stride_z)
    step_x, step_y, step_z = map(c_double, step)
    offset_x, offset_y, offset_z = map(c_double, offset)
    triangles_p = POINTER(c_double)()
    num_triangles = _mc.triangulate(data, isolevel,
                                    dim_x, dim_y, dim_z,
                                    stride_x, stride_y, stride_z,
                                    step_x, step_y, step_z,
                                    offset_x, offset_y, offset_z,
                                    byref(triangles_p))
    triangles = np.fromiter(triangles_p, c_float, num_triangles*2*3*3)
    _mc.free_triangles(triangles_p)
    triangles.shape = (num_triangles, 2, 3, 3)
    vertices = triangles[:,0,:,:]
    normals = triangles[:,1,:,:]
    return vertices, normals
    
    
if __name__ == "__main__":
    data = np.fromfile("input.data", np.uint16)
    data.shape = (64, 64, 93)
    data = data.astype(c_ushort)
    vertices, normals = triangulate(data, (1.0/64, 1.0/64, 1.5/3.2/64), (-0.5, -0.5, -0.5), 1300, ((10,54), (20,44), (20,50)))
    print vertices.shape
    with open("triangles.data", "wb") as outfile:
        outfile.write(vertices.tostring())
    with open("normals.data", "wb") as outfile:
        outfile.write(normals.tostring())
