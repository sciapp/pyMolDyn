from . import algorithm
from .algorithm import ObjectType
from .util.graph import GraphForSplitAndMerge


def start_split_and_merge_pipeline(
    data, mask, atoms, combined_translation_vectors, get_translation_vector, object_type, progress=0
):
    def is_relevant_part(hom_image_data_part):
        return algorithm.is_relevant_part(hom_image_data_part, object_type)

    graph = GraphForSplitAndMerge(data, mask, get_translation_vector, is_relevant_part)
    algorithm.split(data, mask, graph, object_type)
    algorithm.merge(data, graph)
    algorithm.add_periodic_neighbors(graph, progress)
    algorithm.merge_periodic_border(data, graph)
    areas, non_translated_areas, cyclic_area_indices = graph.get_all_areas(
        apply_translation=True, with_non_translated_nodes=True, mark_cyclic_areas=True
    )
    areas_cells, non_translated_areas_cells = map(algorithm.get_domain_area_cells, [areas, non_translated_areas])
    if object_type == ObjectType.DOMAIN:
        algorithm.mark_domain_points(data, non_translated_areas)
        centers = algorithm.calculate_domain_centers(atoms, combined_translation_vectors, non_translated_areas)
        surface_cells = algorithm.get_domain_surface_cells(data, mask, non_translated_areas)

        return (
            centers,
            areas_cells,
            non_translated_areas_cells,
            surface_cells,
            cyclic_area_indices,
        )
    else:
        return areas_cells, non_translated_areas_cells, cyclic_area_indices
