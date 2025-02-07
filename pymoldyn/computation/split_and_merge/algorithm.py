import itertools

import numpy as np

from ...util import message
from ...util.logger import Logger
from .domain_centers import calculate_domain_centers as calc_dom
from .util.node_border_iterator import iterate_node_border_with_adjacent_node_cells
from .util.numpy_extension import find_index_of_first_element_not_equivalent
from .util.pos_bool_type import PosBoolType

it = itertools.count(0, 1)

logger = Logger("computation.split_and_merge.algorithm")


class ObjectType:
    DOMAIN = next(it)
    CAVITY = next(it)


def is_homogenous_split(data_part, mask_part):
    try:
        return PosBoolType(
            find_index_of_first_element_not_equivalent.find_index_of_first_element_not_equivalent(data_part, mask_part)
        )
    except TypeError:
        if "C extension missing" not in logger.logs:
            logger.warn("Falling back to Python functions")
            message.log(
                "Some C extensions could not be loaded, falling back to Python functions."
                " Calculations may be very slow!",
                tag="C extension missing",
            )
        if data_part[0][0][0] == 0:
            if mask_part[0][0][0] == 0:
                ret = np.where(np.logical_or(mask_part != 0, data_part != 0), 1, 0).nonzero()
            else:
                ret = np.where(np.logical_or(mask_part == 0, data_part != 0), 1, 0).nonzero()
        else:
            if mask_part[0][0][0] == 0:
                ret = np.where(np.logical_or(mask_part != 0, data_part == 0), 1, 0).nonzero()
            else:
                ret = np.where(np.logical_or(mask_part == 0, data_part == 0), 1, 0).nonzero()
        try:
            return PosBoolType((ret[0][0], ret[1][0], ret[2][0]))
        except:  # noqa: E722
            return PosBoolType((-1, -1, -1))


def is_homogenous_merge(image_data_part, image_merge_data):
    def sign(x):
        return 1 if x > 0 else -1 if x < 0 else 0

    return sign(image_data_part[0, 0, 0]) == sign(image_merge_data[0, 0, 0])


def is_relevant_part(hom_image_data_part, object_type):
    obj_to_func = {ObjectType.DOMAIN: is_domain_part, ObjectType.CAVITY: is_cavity_part}
    return obj_to_func[object_type](hom_image_data_part)


def is_domain_part(hom_image_data_part):
    return hom_image_data_part[0, 0, 0] == 0


def is_cavity_part(hom_image_data_part):
    return hom_image_data_part[0, 0, 0] < 0


def is_inside_volume(hom_mask_part):
    return not bool(hom_mask_part[0, 0, 0])


def is_neighboring(node1, node2):
    x_, y_, z_ = node1[0]
    w_, h_, d_ = node1[1]
    x, y, z = node2[0]
    w, h, d = node2[1]
    return x - w_ <= x_ <= x + w and y - h_ <= y_ <= y + h and z - d_ <= z_ <= z + d


def split(data, mask, graph, object_type):
    node = ((0, 0, 0), data.shape)
    graph.set_initial_node(node)
    stack = [node]
    while len(stack) > 0:
        pos, dim = stack.pop()
        is_hom = is_homogenous_split(
            data[
                pos[0] : pos[0] + dim[0],
                pos[1] : pos[1] + dim[1],
                pos[2] : pos[2] + dim[2],
            ],
            mask[
                pos[0] : pos[0] + dim[0],
                pos[1] : pos[1] + dim[1],
                pos[2] : pos[2] + dim[2],
            ],
        )
        if not is_hom:
            nodes = graph.split_node((pos, dim), is_hom)
            for node in nodes:
                stack.append(node)
        elif is_relevant_part(
            data[
                pos[0] : pos[0] + dim[0],
                pos[1] : pos[1] + dim[1],
                pos[2] : pos[2] + dim[2],
            ],
            object_type,
        ) or not is_inside_volume(
            mask[
                pos[0] : pos[0] + dim[0],
                pos[1] : pos[1] + dim[1],
                pos[2] : pos[2] + dim[2],
            ]
        ):
            graph.remove_node((pos, dim))
    graph.forbid_splitting()


def merge(data, graph):
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            if not graph.is_merged(node, neighbor):
                pos_node, dim_node = node
                pos_neighbor, dim_neighbor = neighbor
                data_node = data[
                    pos_node[0] : pos_node[0] + dim_node[0],
                    pos_node[1] : pos_node[1] + dim_node[1],
                    pos_node[2] : pos_node[2] + dim_node[2],
                ]
                data_neighbor = data[
                    pos_neighbor[0] : pos_neighbor[0] + dim_neighbor[0],
                    pos_neighbor[1] : pos_neighbor[1] + dim_neighbor[1],
                    pos_neighbor[2] : pos_neighbor[2] + dim_neighbor[2],
                ]
                if is_homogenous_merge(data_node, data_neighbor):
                    graph.merge_nodes(node, neighbor)


def add_periodic_neighbors(graph, progress):
    border_node_translation_vectors = graph.get_border_node_translation_vectors()
    border_nodes = list(border_node_translation_vectors.keys())
    num_nodes = len(border_nodes[:-1])
    for i, n in enumerate(border_nodes[:-1]):
        if progress > 0:
            message.progress(int(progress + (7 / num_nodes) * i))
        for m in border_nodes[i + 1 :]:
            m_x, m_y, m_z = m[0]
            for translation_vector in border_node_translation_vectors[m]:
                translated_node = (
                    (
                        m_x + translation_vector[0],
                        m_y + translation_vector[1],
                        m_z + translation_vector[2],
                    ),
                    m[1],
                )
                if is_neighboring(n, translated_node):
                    graph.add_neighbors(n, [m], translation_vectors=[translation_vector])
                    break


def merge_periodic_border(data, graph):
    for border_node, border_neighbors in graph.iter_border_items():
        for border_neighbor in border_neighbors:
            if not graph.is_merged(border_node, border_neighbor, detect_cyclic_merge=True):
                pos_node, dim_node = border_node
                pos_neighbor, dim_neighbor = border_neighbor
                data_node = data[
                    pos_node[0] : pos_node[0] + dim_node[0],
                    pos_node[1] : pos_node[1] + dim_node[1],
                    pos_node[2] : pos_node[2] + dim_node[2],
                ]
                data_neighbor = data[
                    pos_neighbor[0] : pos_neighbor[0] + dim_neighbor[0],
                    pos_neighbor[1] : pos_neighbor[1] + dim_neighbor[1],
                    pos_neighbor[2] : pos_neighbor[2] + dim_neighbor[2],
                ]
                if is_homogenous_merge(data_node, data_neighbor):
                    graph.merge_nodes(border_node, border_neighbor)


def mark_domain_points(data, areas):
    for i, area in enumerate(areas):
        for node in area:
            x, y, z = node[0]
            w, h, d = node[1]
            data[x : x + w, y : y + h, z : z + d] = -(i + 1)


def calculate_domain_centers(atoms, combined_translation_vectors, areas):
    combined_translation_vectors_tuples = [tuple(t) for t in combined_translation_vectors]
    areas = [list(a) for a in areas]
    return calc_dom.calculate_domain_centers(atoms, combined_translation_vectors_tuples, areas)


def get_domain_area_cells(areas):
    cell_positions = [
        [
            (pos[0] + x, pos[1] + y, pos[2] + z)
            for pos, dim in area
            for x, y, z in itertools.product(*(range(c) for c in dim))
        ]
        for area in areas
    ]
    return cell_positions


def get_domain_surface_cells(data, mask, areas):
    domain = None

    def func(border_x, border_y, border_z, adjacent_node_cells):
        if bool(data[border_x, border_y, border_z]) or bool(mask[border_x, border_y, border_z]):
            for n in adjacent_node_cells:
                domain.add(n)

    domains = []
    for area in areas:
        domain = set()
        for node in area:
            iterate_node_border_with_adjacent_node_cells(node, func)
        domains.append(list(domain))
    return domains
