import itertools as it

from ....util.logger import Logger
from .node_border_iterator import iterate_node_border

logger = Logger("computation.split_and_merge.util.graph")


class MergeGroup(object):
    """
    Class that collects a group of homogenous nodes. Groups that are divided by the periodic border can be
    organized in subgroups.
    The object is intended to be used in two phases:

        1.  Collecting nodes: All nodes are collected in one subgroup. Multiple subgroups are not allowed in this phase.
        2.  Merging with other MergeGroup objects: Two objects can be merged resulting in one object with separate
            subgroups. When merging has been started, no additional nodes can be added.

    """

    class SharedAttributes(object):
        """
        Instances of this class can be used to store key value pairs (like in dicts). One instance can be shared between
        multiple MergeGroup instances so an attribute update will automtically be published to all merge groups that
        hold a reference to the same shared attributes object.
        """

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def __contains__(self, item):
            return item in self.__dict__

    def __init__(self, initial_node=None):
        self._shared_attributes = MergeGroup.SharedAttributes(
            subgroups=[],
            translation_vectors=[],  # offset that can be applied to the i-th subgroup to merge it with the next
            # subgroup in the list
            all_merge_groups=[self],
            is_cyclic=False,
        )
        self._index_of_primary_subgroup = None  # Saves the index of the first subgroup in the subgroups list that has
        # been assigned to this MergeGroup object
        if initial_node is not None:
            self.add(set([initial_node]))

    def add(self, nodes):
        """
        Adds nodes from another MergeGroup or a single node.
        """
        if len(self._subgroups) > 1:
            raise AddingNodesNotAllowedError("In the merge phase adding nodes is not longer possible.")

        if isinstance(nodes, type(self)):
            # only the nodes of the second merge group are collected. That is NOT a merging operation!
            self.add(list(nodes))
        else:
            if not isinstance(nodes, (set, list)):
                nodes = [nodes]
            if len(self._subgroups) == 0:
                self._subgroups.append(set())
                self._index_of_primary_subgroup = 0
            self._subgroups[0].update(nodes)

    def merge(self, merge_group, translation_vector):
        """
        Merges two MergeGroups by adding the _subgroups of the other merge_group respectively. Therefore, both
        MergeGroups are changed.
        It is supposed that the given translation_vector can be applied on the primary subgroup of self to merge it with
        the primary subgroup of merge_group.
        """

        def subtract_vector_list(translation_vector, *vector_lists):
            for vector in it.chain(*vector_lists):
                translation_vector = tuple(tc - vc for tc, vc in zip(translation_vector, vector))
            return translation_vector

        subgroup_count_before_merge = len(self._subgroups)

        self._subgroups.extend(merge_group._subgroups)
        subtraction_vectors = self._translation_vectors[self._index_of_primary_subgroup :]
        subtraction_vectors.extend(merge_group._translation_vectors[: merge_group._index_of_primary_subgroup])
        self._translation_vectors.append(subtract_vector_list(translation_vector, subtraction_vectors))
        self._translation_vectors.extend(merge_group._translation_vectors)

        self._all_merge_groups.extend(merge_group._all_merge_groups)
        merge_group._update_all_merge_groups(self._shared_attributes, subgroup_count_before_merge)

    def set_cyclic(self):
        self._shared_attributes.is_cyclic = True

    def _update_all_merge_groups(self, shared_attributes, index_shift):
        for merge_group in self._all_merge_groups[:]:
            merge_group._shared_attributes = shared_attributes
            merge_group._index_of_primary_subgroup += index_shift

    def __getattr__(self, attr):
        if attr.startswith("_"):
            if hasattr(self, "_shared_attributes") and attr[1:] in self._shared_attributes:
                return getattr(self._shared_attributes, attr[1:])
        return super(MergeGroup, self).__getattribute__(attr)

    def __contains__(self, node):
        return any(node in subgroup for subgroup in self._subgroups)

    def __len__(self):
        return sum(len(subgroup) for subgroup in self._subgroups)

    def __delitem__(self, item):
        for subgroup in self._subgroups:
            if item in subgroup:
                del subgroup[item]

    def __iter__(self):
        """
        Iterator for the nodes of all subgroups 'as is' -> translation is not applied.
        """
        return it.chain(*(subgroup for subgroup in self._subgroups))

    def iter_with_applied_translation(
        self,
        iter_with_non_translated_nodes=False,
        keep_largest_volume_within_cell=False,
    ):
        """
        Iterator for the nodes of all subgroups with applied translation -> the result is a continuous volume
        """

        def create_node_generator(subgroup, translation_vector):
            # generator expression must be created in a nested function to avoid late variable binding problems with
            # "combined_translation_vector"; without a nested function all generator expressions would get the last
            # value that was assigned to "combined_translation_vector" during the loop iterations in the outer function
            return ((tuple(nc - tc for nc, tc in zip(pos, translation_vector)), dim) for pos, dim in subgroup)

        def get_generators_from_start_index(index, reverse=False):
            generators = []
            if not reverse:
                factor = 1
                subgroups = self._subgroups[index:]
                translation_vectors = self._translation_vectors[index:]
                combined_translation_vector = (0, 0, 0)
            else:
                factor = -1
                subgroups = self._subgroups[index - 1 :: -1] if index > 0 else []
                translation_vectors = self._translation_vectors[index - 2 :: -1] if index > 1 else []
                combined_translation_vector = (
                    tuple(-c for c in self._translation_vectors[index - 1]) if index > 0 else (0, 0, 0)
                )
            iterator = it.zip_longest(subgroups, translation_vectors)
            for subgroup, translation_vector in iterator:
                generator = create_node_generator(subgroup, combined_translation_vector)
                if iter_with_non_translated_nodes:
                    generators.append(zip(subgroup, generator))
                else:
                    generators.append(generator)
                if translation_vector is not None:
                    combined_translation_vector = tuple(
                        cc + factor * tc for cc, tc in zip(combined_translation_vector, translation_vector)
                    )
            return generators

        if keep_largest_volume_within_cell:
            index_of_non_translated_subgroup = max(range(len(self._subgroups)), key=lambda i: len(self._subgroups[i]))
        else:
            index_of_non_translated_subgroup = self._index_of_primary_subgroup
        generators = []
        backwards_generators = get_generators_from_start_index(index_of_non_translated_subgroup, reverse=True)
        generators.extend(list(reversed(backwards_generators)))
        forwards_generators = get_generators_from_start_index(index_of_non_translated_subgroup)
        generators.extend(forwards_generators)
        return it.chain(*generators)

    @property
    def is_cyclic(self):
        return self._is_cyclic


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

    def items(self):
        return self.nodes.items()

    def itervalues(self):
        return self.nodes.itervalues()


class GraphForSplitAndMerge(Graph):
    """
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
    """

    def __init__(self, data, mask, get_translation_vector, is_relevant_part, initial_node=None):
        Graph.__init__(self)
        self.data = data
        self.mask = mask
        self.get_translation_vector = get_translation_vector
        self.is_relevant_part = is_relevant_part
        self.merged_nodes = {}
        self.border_nodes = None
        self.border_node_translation_vectors = None
        self.border_node_pair_translations = None
        self.split_allowed = True
        self.adding_non_periodic_neighbors_allowed = True
        self.merging_non_periodic_neighbors_allowed = True
        self.initial_node_set = False
        if initial_node is not None:
            self.set_initial_node(initial_node)

    def set_initial_node(self, initial_node):
        if not self.initial_node_set:
            self.add_node(initial_node, set())
            self.initial_node_set = True
        else:
            raise InitialNodeAlreadySetError

    def add_node(self, node, potential_neighbors=None):
        neighbors = self.__find_neighbors(node, potential_neighbors)
        Graph.add_node(self, node, neighbors)
        # The new node must be merged with itself because later other nodes could share the set of merged nodes:
        self.merged_nodes[node] = MergeGroup(node)

    def add_neighbors(self, node, neighbors, translation_vectors=None):
        periodic_border_relationship = translation_vectors is not None
        if not self.adding_non_periodic_neighbors_allowed:
            if node not in self.nodes:
                raise AddingNodesNotAllowedError
            elif not periodic_border_relationship:
                raise AddingNonPeriodicNeighborsNotAllowedError
        Graph.add_neighbors(self, node, neighbors)
        if periodic_border_relationship:
            self.adding_non_periodic_neighbors_allowed = False
            if self.border_nodes is None:
                self.__mark_border_nodes()
            self.border_nodes[node] |= set(neighbors)
            for neighbor, translation_vector in zip(neighbors, translation_vectors):
                self.border_node_pair_translations[(neighbor, node)] = translation_vector
                self.border_node_pair_translations[(node, neighbor)] = tuple(-c for c in translation_vector)

    def remove_node(self, node):
        Graph.remove_node(self, node)
        del self.merged_nodes[node]

    def split_node(self, node, split_point_rel):
        """
        split_point_rel is that point relative to the left top corner of the node that contains the first inhomogeneity.
        It is implicated that the node data is stored in C order. Therefore, it is possible to split the node into 4
        homogeneous and 4 potential inhomogeneous sub nodes which causes a great speedup of the whole
        algorithm.
        """
        if self.split_allowed:
            self.border_nodes = None
            self.border_node_translation_vectors = None
            self.border_node_pair_translations = None
            x, y, z = node[0]
            w, h, d = node[1]
            x_inh, y_inh, z_inh = split_point_rel

            potential_new_homogen_nodes = (
                ((x, y, z), (x_inh + 1, y_inh + 1, z_inh)),
                ((x, y, z + z_inh), (x_inh + 1, y_inh, d - z_inh)),
                ((x, y + y_inh + 1, z), (x_inh, h - y_inh - 1, z_inh)),
                ((x, y + y_inh, z + z_inh), (x_inh, h - y_inh, d - z_inh)),
            )

            potential_new_inhomogen_nodes = (
                ((x + x_inh + 1, y, z), (w - x_inh - 1, y_inh + 1, z_inh)),
                ((x + x_inh + 1, y, z + z_inh), (w - x_inh - 1, y_inh, d - z_inh)),
                ((x + x_inh, y + y_inh + 1, z), (w - x_inh, h - y_inh - 1, z_inh)),
                ((x + x_inh, y + y_inh, z + z_inh), (w - x_inh, h - y_inh, d - z_inh)),
            )

            def get_relevant_nodes(potential_nodes, hom_nodes=False):
                new_nodes = []
                for n in potential_nodes:
                    x, y, z = n[0]
                    w, h, d = n[1]
                    if w > 0 and h > 0 and d > 0:
                        # a => b
                        if not hom_nodes or (
                            self.is_relevant_part(self.data[x : x + w, y : y + h, z : z + d])
                            and not bool(self.mask[x, y, z])
                        ):
                            new_nodes.append(n)
                return new_nodes

            new_homogen_nodes = get_relevant_nodes(potential_new_homogen_nodes, hom_nodes=True)
            new_inhomogen_nodes = get_relevant_nodes(potential_new_inhomogen_nodes)
            all_new_nodes = set(new_homogen_nodes) | set(new_inhomogen_nodes)

            potential_neighbors = self.get_neighbors(node) | all_new_nodes
            self.remove_node(node)
            for n in all_new_nodes:
                self.add_node(n, potential_neighbors - set([n]))

            return new_inhomogen_nodes
        else:
            raise SplitNotAllowedError

    def get_border_nodes(self):
        if self.border_nodes is None:
            self.__mark_border_nodes()
        return self.border_nodes.keys()

    def get_border_node_translation_vectors(self):
        if self.border_node_translation_vectors is None:
            self.__mark_border_nodes()
        return self.border_node_translation_vectors

    def __mark_border_nodes(self):
        translation_vectors = None

        def func(border_x, border_y, border_z):
            try:
                if bool(self.mask[border_x, border_y, border_z]):
                    translation_vectors.add(  # Attribute error?
                        tuple(self.get_translation_vector((border_x, border_y, border_z)))
                    )
            except Exception as e:
                logger.error("Error when creating translation vectors: {}".format(e))

        self.border_nodes = {}
        self.border_node_translation_vectors = {}
        self.border_node_pair_translations = {}
        for node in self:
            node_x, node_y, node_z = node[0]
            node_w, node_h, node_d = node[1]
            for x, y, z in it.product(
                (node_x - 1, node_x + node_w),
                (node_y - 1, node_y + node_h),
                (node_z - 1, node_z + node_d),
            ):
                if bool(self.mask[x, y, z]):
                    translation_vectors = set()
                    iterate_node_border(node, func)
                    self.border_nodes[node] = set()
                    self.border_node_translation_vectors[node] = translation_vectors
                    break

    def forbid_splitting(self):
        self.split_allowed = False

    def merge_nodes(self, node1, node2):
        """
        Only nodes can be merged that are neighboring.
        """

        # Neighbors?
        if node2 not in self.nodes[node1]:
            raise NotNeighboringError
        self.forbid_splitting()
        if not self.is_merged(node1, node2, detect_cyclic_merge=True):
            separated_by_periodic_boundary_condition = (
                self.border_nodes is not None and node1 in self.border_nodes and node2 in self.border_nodes[node1]
            )
            if not separated_by_periodic_boundary_condition:
                if not self.merging_non_periodic_neighbors_allowed:
                    raise MergingNonBorderNodesNotAllowedError
                # Record all merged nodes of node2 as merged nodes of node1 (node2 is already included)
                self.merged_nodes[node1].add(self.merged_nodes[node2])
                # Since the merged nodes of node1 have a reference to self.merged_nodes[node1], they have been already
                # updated. So, it is only necessary to update the merged_nodes of node2 (which contain node2 already).
                for merged_node in self.merged_nodes[node2]:
                    self.merged_nodes[merged_node] = self.merged_nodes[node1]
            else:
                self.merging_non_periodic_neighbors_allowed = False
                self.merged_nodes[node1].merge(
                    self.merged_nodes[node2],
                    self.border_node_pair_translations[(node1, node2)],
                )
        return node2 in self.merged_nodes[node1]

    def is_merged(self, node1, node2, detect_cyclic_merge=False):
        # If node2 is not merged with node1 than node1 is not merged with node2, neither.
        is_merged = node2 in self.merged_nodes[node1]
        if is_merged and detect_cyclic_merge and self.merged_nodes[node1] is self.merged_nodes[node2]:
            self.merged_nodes[node1].set_cyclic()
        return is_merged

    def get_all_areas(
        self,
        apply_translation=False,
        with_non_translated_nodes=False,
        mark_cyclic_areas=False,
    ):
        """
        Returns a list of sets, each describing a merged area of nodes. If "apply_translation" is set to True,
        all subgroups of an area are translated with respect to the periodic border condition. As a result, all areas
        are contiguous in space. If "with_non_translated_nodes" is set additionally, a second list is returned that
        contains the same areas without applied translations. If "mark_cyclic_areas" is set to True, the function has a
        further list as second/third return value indicating which areas (given by index) are cyclic (have infinite
        extent).
        """
        if self.split_allowed:
            return []
        areas = []
        # Saves non translated areas if "apply_translation" and "with_non_translated_nodes" are set to true
        alt_areas = [] if with_non_translated_nodes else None
        cyclic_areas = [] if mark_cyclic_areas else None
        visited_nodes = set()
        for node in self:
            if node not in visited_nodes:
                area = set()
                if apply_translation:
                    node_iterator = self.merged_nodes[node].iter_with_applied_translation(
                        iter_with_non_translated_nodes=True,
                        keep_largest_volume_within_cell=True,
                    )
                    if with_non_translated_nodes:
                        alt_area = set()
                        for merged_node, translated_node in node_iterator:
                            area.add(translated_node)
                            alt_area.add(merged_node)
                            visited_nodes.add(merged_node)
                        alt_areas.append(alt_area)
                    else:
                        for merged_node, translated_node in node_iterator:
                            area.add(translated_node)
                            visited_nodes.add(merged_node)
                else:
                    node_iterator = self.merged_nodes[node]
                    for merged_node in node_iterator:
                        area.add(merged_node)
                        visited_nodes.add(merged_node)
                areas.append(area)
                if mark_cyclic_areas and self.merged_nodes[node].is_cyclic:
                    cyclic_areas.append(len(areas) - 1)
        if apply_translation and with_non_translated_nodes and mark_cyclic_areas:
            return areas, alt_areas, cyclic_areas
        elif mark_cyclic_areas:
            return areas, cyclic_areas
        else:
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
            if x - w_ <= x_ <= x + w and y - h_ <= y_ <= y + h and z - d_ <= z_ <= z + d:
                neighbors.add(n)
        return neighbors

    def iter_border_items(self):
        self.get_border_nodes()  # ensure that self.border_nodes is set correctly
        return self.border_nodes.items()


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


class AddingNodesNotAllowedError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class AddingNonPeriodicNeighborsNotAllowedError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class MergingNonBorderNodesNotAllowedError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
