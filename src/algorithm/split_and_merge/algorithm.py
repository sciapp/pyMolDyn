from algorithm.split_and_merge.domain_centers.calculate_domain_centers import calculate_domain_centers as calc_dom
from algorithm.split_and_merge.util.pos_bool_type import PosBoolType
from algorithm.split_and_merge.util.numpy_extension.find_index_of_first_element_not_equivalent import find_index_of_first_element_not_equivalent as find_index_of_first_element_not_equivalent_extension
from algorithm.split_and_merge.util.node_border_iterator import iterate_node_border_with_adjacent_node_cells


def is_equivalent(a, b):
    return (not a or b) and (not b or a)

def is_homogenous_split(data_part, mask_part):
    return PosBoolType(find_index_of_first_element_not_equivalent(data_part, mask_part))

def is_homogenous_merge(data_part, merge_data):
    return is_equivalent(data_part[0, 0, 0], merge_data[0, 0, 0])

def is_atom_part(hom_data_part):
    return bool(hom_data_part[0, 0, 0])

def is_inside_volume(hom_mask_part):
    return not bool(hom_mask_part[0, 0, 0])

def is_neighboring(node1, node2):
    x_, y_, z_ = node1[0]
    w_, h_, d_ = node1[1]
    x,  y,  z  = node2[0]
    w,  h,  d  = node2[1]
    return x-w_ <= x_ <= x+w and y-h_ <= y_ <= y+h and z-d_ <= z_ <= z+d


def split(data, mask, graph):
    node = ((0, 0, 0), data.shape)
    graph.set_initial_node(node)
    stack = [node]
    while len(stack) > 0:
        pos, dim = stack.pop()
        is_hom = is_homogenous_split(data[pos[0]:pos[0]+dim[0], pos[1]:pos[1]+dim[1], pos[2]:pos[2]+dim[2]], mask[pos[0]:pos[0]+dim[0], pos[1]:pos[1]+dim[1], pos[2]:pos[2]+dim[2]])
        if not is_hom:
            nodes = graph.split_node((pos, dim), is_hom)
            for node in nodes:
                stack.append(node)
        elif is_atom_part(data[pos[0]:pos[0]+dim[0], pos[1]:pos[1]+dim[1], pos[2]:pos[2]+dim[2]]) or not is_inside_volume(mask[pos[0]:pos[0]+dim[0], pos[1]:pos[1]+dim[1], pos[2]:pos[2]+dim[2]]):
            graph.remove_node((pos, dim))
            
def add_periodic_neighbors(graph):
    border_node_translation_vectors = graph.get_border_node_translation_vectors()
    border_nodes = border_node_translation_vectors.keys()
    for i, n in enumerate(border_nodes[:-1]):
        for m in border_nodes[i+1:]:
            m_x, m_y, m_z = m[0]
            for translation_vector in border_node_translation_vectors[m]:
                translated_node = ((m_x+translation_vector[0], m_y+translation_vector[1], m_z+translation_vector[2]), m[1])
                if is_neighboring(n, translated_node):
                    graph.add_neighbors(n, [m])
                    break

def merge(data, graph):
    for node, neighbors in graph.iteritems():
        for neighbor in neighbors:
            if not graph.is_merged(node, neighbor):
                pos_node, dim_node = node
                pos_neighbor, dim_neighbor = neighbor
                data_node = data[pos_node[0]:pos_node[0]+dim_node[0], pos_node[1]:pos_node[1]+dim_node[1], pos_node[2]:pos_node[2]+dim_node[2]]
                data_neighbor = data[pos_neighbor[0]:pos_neighbor[0]+dim_neighbor[0], pos_neighbor[1]:pos_neighbor[1]+dim_neighbor[1], pos_neighbor[2]:pos_neighbor[2]+dim_neighbor[2]]
                if is_homogenous_merge(data_node, data_neighbor):
                    graph.merge_nodes(node, neighbor)
                    
def calculate_domain_centers(atoms, combined_translation_vectors, areas):
    return calc_dom(atoms, combined_translation_vectors, areas)
                    
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
