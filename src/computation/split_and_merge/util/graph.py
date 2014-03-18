import itertools as it
from computation.split_and_merge.util.node_border_iterator import iterate_node_border


class Graph(object):
    def __init__(self):
        self.nodes = {}
        
    def add_node(self, node, neighbors=None):
        if neighbors is None:
            neighbors = set()
        else:
            neighbors = set(neighbors)
            
        if node in self.nodes:
            self.remove_node(node)
        
        self.nodes[node] = set()
        self.add_neighbors(node, neighbors)
        
    def add_neighbors(self, node, neighbors):
        for neighbor in neighbors:
            if neighbor in self.nodes:
                self.nodes[neighbor].add(node)
            else:
                self.add_node(neighbor, [node])
        self.nodes[node] |= set(neighbors)
        
    def remove_node(self, node):
        neighbors = self.nodes[node]
        self.remove_neighbors(node, self.nodes[node])
        del self.nodes[node]
        return neighbors
    
    def remove_neighbors(self, node, neighbors):
        for neighbor in neighbors:
            self.nodes[neighbor] -= set([node])
        self.nodes[node] -= set(neighbors)
        return self.nodes[node]
    
    def get_neighbors(self, node):
        return self.nodes[node]
    
    def __contains__(self, node):
        return node in self.nodes
    
    def __len__(self):
        return len(self.nodes)
    
    def __iter__(self):
        return self.nodes.__iter__()
    
    def iterkeys(self):
        return self.nodes.iterkeys()
    
    def iteritems(self):
        return self.nodes.iteritems()
    
    def itervalues(self):
        return self.nodes.itervalues()
    
    
class GraphForSplitAndMerge(Graph):
    '''
    Nodes must be tuples of the format ((x, y, z), (width, height, depth)).
    Graph class which starts with just one initial node. That node can be split
    multiple times at a specified split point (resulting in max 8 sub nodes).
    Neighboring relationships of the sub nodes are determined automatically.
    After the split phase, boundary nodes can be detected. If periodic boundary
    conditions should be considered, the neighboring relationships can be updated
    manually with the found boundary nodes.
    Afterwards, single nodes can be merged together. Internally, they stay as
    single nodes and merges are logged with other data structures (sets).
    The split method can only be used until merge is called for the first time!
    '''
    
    def __init__(self, data, mask, get_translation_vector, initial_node=None):
        Graph.__init__(self)
        self.data = data
        self.mask = mask
        self.get_translation_vector = get_translation_vector
        self.merged_nodes = {}
        self.border_nodes = None
        self.split_allowed = True
        self.initial_node_set = False
        if initial_node is not None:
            self.set_initial_node(initial_node)
        
    def set_initial_node(self, initial_node):
        if self.initial_node_set == False:
            self.add_node(initial_node, set())
            self.initial_node_set = True
        else:
            raise InitialNodeAlreadySetError
        
    def add_node(self, node, potential_neighbors=None):
        neighbors = self.__find_neighbors(node, potential_neighbors)
        Graph.add_node(self, node, neighbors)
        # The new node must be merged with itself because later other nodes could share the set of merged nodes: 
        self.merged_nodes[node] = set([node])
        
    def remove_node(self, node):
        Graph.remove_node(self, node)
        del self.merged_nodes[node]
        
    def split_node(self, node, split_point_rel):
        '''
        split_point_rel is that point relative to the left top corner of the node that contains the first inhomogeneity.
        It is implicated that the node data is stored in C order. Therefore, it is possible to split the node into 4
        homogeneous and 4 potential inhomogeneous sub nodes to speed which causes a great speedup of the whole algorithm.
        '''
        if self.split_allowed:
            self.border_nodes = None
            x, y, z             = node[0]
            w, h, d             = node[1]
            x_inh, y_inh, z_inh = split_point_rel
                        
            potential_new_homogen_nodes   = (((x,         y,         z      ), (x_inh+1,     y_inh+1,   z_inh)),
                                             ((x,         y,         z+z_inh), (x_inh+1,     y_inh,   d-z_inh)),
                                             ((x,         y+y_inh+1, z      ), (x_inh,     h-y_inh-1,   z_inh)),
                                             ((x,         y+y_inh,   z+z_inh), (x_inh,     h-y_inh,   d-z_inh)))
                                             
            potential_new_inhomogen_nodes = (((x+x_inh+1, y,         z      ), (w-x_inh-1,   y_inh+1,   z_inh)),
                                             ((x+x_inh+1, y,         z+z_inh), (w-x_inh-1,   y_inh,   d-z_inh)),
                                             ((x+x_inh,   y+y_inh+1, z      ), (w-x_inh,   h-y_inh-1,   z_inh)),
                                             ((x+x_inh,   y+y_inh,   z+z_inh), (w-x_inh,   h-y_inh,   d-z_inh)))                         
            
            def get_relevant_nodes(potential_nodes, hom_nodes=False):
                new_nodes = []
                for n in potential_nodes:
                    x, y, z = n[0]
                    w, h, d = n[1]
                    if w > 0 and h > 0 and d > 0:
                        if not hom_nodes or (not bool(self.data[x, y, z]) and not bool(self.mask[x, y, z])):   # a => b
                            new_nodes.append(n)
                return new_nodes
            
            new_homogen_nodes   = get_relevant_nodes(potential_new_homogen_nodes, hom_nodes=True)
            new_inhomogen_nodes = get_relevant_nodes(potential_new_inhomogen_nodes)
            all_new_nodes       = set(new_homogen_nodes) | set(new_inhomogen_nodes)
            
            potential_neighbors = self.get_neighbors(node) | all_new_nodes
            self.remove_node(node)
            for n in all_new_nodes:
                self.add_node(n, potential_neighbors - set([n]))
            
            return new_inhomogen_nodes
        else:
            raise SplitNotAllowedError
        
    def get_border_node_translation_vectors(self):
        if self.border_nodes is None:
            self.__mark_border_nodes()
        return self.border_nodes
        
    def __mark_border_nodes(self):
        translation_vectors = None
        
        def func(border_x, border_y, border_z):
            if bool(self.mask[border_x, border_y, border_z]):
                translation_vectors.add(tuple(self.get_translation_vector((border_x, border_y, border_z))))
                
        self.border_nodes = {}
        for node in self:
            node_x, node_y, node_z = node[0]
            node_w, node_h, node_d = node[1]
            for x, y, z in it.product((node_x-1, node_x+node_w), (node_y-1, node_y+node_h), (node_z-1, node_z+node_d)):
                if(bool(self.mask[x, y, z])):
                    translation_vectors = set()
                    iterate_node_border(node, func)
                    self.border_nodes[node] = translation_vectors    
                    break
            
    def merge_nodes(self, node1, node2):
        '''
        Only nodes can be merged that are neighboring.
        '''
        # Neighbors?
        if node2 in self.nodes[node1]:
            self.split_allowed = False
            # If node2 is not merged with node1 than node1 is not merged with node2, neither. 
            if node2 not in self.merged_nodes[node1]:
                # Record all merged nodes of node2 as merged nodes of node1 (node2 is already included)
                self.merged_nodes[node1] |= self.merged_nodes[node2]
                # Since the merged nodes of node1 have a reference to self.merged_nodes[node1], they have been already updated.
                # So, it is only necessary to update the merged_nodes of node2 (which contain node2 already).
                for merged_node in self.merged_nodes[node2]:
                    self.merged_nodes[merged_node] = self.merged_nodes[node1]
        else:
            raise NotNeighboringError
        
    def is_merged(self, node1, node2):
        return node2 in self.merged_nodes[node1]
        
    def get_all_areas(self):
        '''
        Returns a list of sets, each describing a merged area of nodes.
        '''
        if self.split_allowed:
            return []
        areas = []
        visited_nodes = set()
        for node in self:
            if node not in visited_nodes:
                area = set([node])
                for merged_node in self.merged_nodes[node]:
                    area.add(merged_node)
                    visited_nodes.add(merged_node)
                areas.append(area)
        return areas
    
    def __find_neighbors(self, node, potential_neighbors):
        x_, y_, z_ = node[0]
        w_, h_, d_ = node[1]
        neighbors = set()
        if potential_neighbors is None:
            potential_neighbors = self.nodes.keys()
        for n in potential_neighbors:
            x, y, z = n[0]
            w, h, d = n[1]
            if x-w_ <= x_ <= x+w and y-h_ <= y_ <= y+h and z-d_ <= z_ <= z+d:
                neighbors.add(n)
        return neighbors
        
        
class NotNeighboringError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
    
class InitialNodeAlreadySetError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
    
    
class SplitNotAllowedError(Exception):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return repr(self.msg)
