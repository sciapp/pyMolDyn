from computation.split_and_merge import algorithm
from computation.split_and_merge.algorithm import ObjectType
from computation.split_and_merge.util.graph import GraphForSplitAndMerge


def start_split_and_merge_pipeline(data, mask, atoms, combined_translation_vectors,
                                   get_translation_vector, object_type):
    def is_relevant_part(hom_image_data_part):
        return algorithm.is_relevant_part(hom_image_data_part, object_type)

    graph = GraphForSplitAndMerge(data, mask, get_translation_vector, is_relevant_part)

    algorithm.split(data, mask, graph, object_type)
    algorithm.merge(data, graph)
    algorithm.add_periodic_neighbors(graph)
    algorithm.merge_periodic_border(data, graph)
    areas, non_translated_areas, areas_translation_vectors, cyclic_area_indices = graph.get_all_areas(apply_translation=True,
                                                                                                      with_non_translated_nodes=True,
                                                                                                      mark_cyclic_areas=True)
    # algorithm.mark_domain_points(data, non_translated_areas)

    # centers = algorithm.calculate_domain_centers(atoms, combined_translation_vectors, non_translated_areas)
    # surface_cells = algorithm.get_domain_surface_cells(data, mask, non_translated_areas)

    centers, surface_cells = None, None

    return centers, areas, non_translated_areas, areas_translation_vectors, surface_cells
