#!/usr/bin/env python3

import struct
import zlib

import numpy as np
import numpy.linalg as la


def cartesian(arrays, out=None):
    # editorconfig-checker-disable
    """
    Generate a cartesian product of input arrays.

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.

    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.

    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6],
           [1, 4, 7],
           [1, 5, 6],
           [1, 5, 7],
           [2, 4, 6],
           [2, 4, 7],
           [2, 5, 6],
           [2, 5, 7],
           [3, 4, 6],
           [3, 4, 7],
           [3, 5, 6],
           [3, 5, 7]])

    """
    # editorconfig-checker-enable

    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)

    m = n / arrays[0].size
    out[:, 0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m, 1:])
        for j in range(1, arrays[0].size):
            out[j * m : (j + 1) * m, 1:] = out[0:m, 1:]
    return out


def to_png(image):
    """
    Return a binary png image for a given image stored as two-dimensional numpy
    array
    """
    width, height, _ = image.shape
    image.shape = np.prod(image.shape)
    width_byte_4 = width * 4
    data_iterator = (
        b"\x00" + image[span : span + width_byte_4].tostring()
        for span in range((height - 1) * width * 4, -1, -width_byte_4)
    )
    raw_data = bytes().join(data_iterator)

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return struct.pack(b"!I", len(data)) + chunk_head + struct.pack("!I", 0xFFFFFFFF & zlib.crc32(chunk_head))

    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            png_pack(b"IHDR", struct.pack(b"!2I5B", width, height, 8, 6, 0, 0, 0)),
            png_pack(b"IDAT", zlib.compress(raw_data, 9)),
            png_pack(b"IEND", b""),
        ]
    )


def write_png(image, filename):
    """Write an image stored as two-dimensional numpy array to a file"""
    with open(filename, "wb") as out:
        out.write(to_png(image))


def intensities_to_image(intensities):
    """
    Return a 32bit RGBA image representing the given intensities
    """
    width, height = intensities.shape
    image = np.zeros((width, height, 4), dtype=np.uint8)
    image[:, :, 2] = image[:, :, 1] = image[:, :, 0] = normalized(intensities.T) * 255
    image[:, :, 3] = 255
    return image


def intensities_to_image_unnormalized(intensities):
    """
    Return a 32bit RGBA image representing the given intensities
    """
    width, height = intensities.shape
    image = np.zeros((width, height, 4), dtype=np.uint8)
    image[:, :, 2] = image[:, :, 1] = image[:, :, 0] = intensities.T * 255
    image[:, :, 3] = 255
    return image


def normalized(array):
    """
    Return a normalized version of a numpy array, with values ranging from
    0 to 1
    """
    ptp = np.ptp(array)
    if ptp == 0:
        ptp = 1
    return (array - np.min(array)) / ptp


def create_rotation_matrix(angle, x, y, z):
    x, y, z = np.array((x, y, z)) / la.norm((x, y, z))
    matrix = np.zeros((3, 3), dtype=np.float32)
    cos = np.cos(angle)
    sin = np.sin(angle)
    matrix[0, 0] = x * x * (1 - cos) + cos
    matrix[1, 0] = x * y * (1 - cos) + sin * z
    matrix[0, 1] = x * y * (1 - cos) - sin * z
    matrix[2, 0] = x * z * (1 - cos) - sin * y
    matrix[0, 2] = x * z * (1 - cos) + sin * y
    matrix[1, 1] = y * y * (1 - cos) + cos
    matrix[1, 2] = y * z * (1 - cos) - sin * x
    matrix[2, 1] = y * z * (1 - cos) + sin * x
    matrix[2, 2] = z * z * (1 - cos) + cos
    return matrix


def create_perspective_projection_matrix(
    vertical_field_of_view,
    aspect_ratio,
    near_clipping_pane_distance,
    far_clipping_pane_distance,
):
    """
    Creates a perspective projection matrix as described at:
        http://www.opengl.org/sdk/docs/man2/xhtml/gluPerspective.xml
    """
    matrix = np.zeros((4, 4), dtype=np.float32)
    f = 1 / np.tan(0.5 * vertical_field_of_view)
    matrix[0, 0] = f / aspect_ratio
    matrix[1, 1] = f
    matrix[2, 2] = (near_clipping_pane_distance + far_clipping_pane_distance) / (
        near_clipping_pane_distance - far_clipping_pane_distance
    )
    matrix[2, 3] = (
        2
        * near_clipping_pane_distance
        * far_clipping_pane_distance
        / (near_clipping_pane_distance - far_clipping_pane_distance)
    )
    matrix[3, 2] = -1
    return matrix


def create_orthogonal_projection_matrix(left, right, bottom, top, near, far):
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 2 / (right - left)
    matrix[1, 1] = 2 / (top - bottom)
    matrix[2, 2] = 2 / (far - near)
    matrix[0, 3] = (right + left) / (right - left)
    matrix[1, 3] = (top + bottom) / (top - bottom)
    matrix[2, 3] = (far + near) / (far - near)
    matrix[3, 3] = 1
    return matrix


def create_rotation_matrix_homogenous(angle, x, y, z):
    matrix = np.eye(4, 4, dtype=np.float32)
    matrix[:3, :3] = create_rotation_matrix(angle, x, y, z)
    return matrix


def create_translation_matrix_homogenous(x, y, z):
    matrix = np.eye(4, 4, dtype=np.float32)
    matrix[:3, 3] = (x, y, z)
    return matrix


def normalize(x):
    return x / la.norm(x)


def create_look_at_matrix(eye, center, up):
    forward = normalize(center - eye)
    up = normalize(up)
    s = np.cross(forward, up)
    upward = np.cross(s, forward)

    matrix = np.eye(4, 4, dtype=np.float32)
    matrix[0, :3] = s
    matrix[1, :3] = upward
    matrix[2, :3] = -forward
    matrix[:3, 3] = -eye
    return matrix
