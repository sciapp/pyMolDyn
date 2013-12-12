from algorithm.split_and_merge import algorithm
from algorithm.split_and_merge.util.graph import GraphForSplitAndMerge


def start_split_and_merge_pipeline(data, mask, atoms, combined_translation_vectors):
    graph = GraphForSplitAndMerge(data, mask, get_translation_vector)
    
    algorithm.split(data, mask, graph)
    algorithm.add_periodic_neighbors(graph)
    algorithm.merge(data, graph)
    areas = graph.get_all_areas()
    algorithm.mark_domain_points(data, areas)
    
    centers = algorithm.calculate_domain_centers(atoms, combined_translation_vectors, areas)
    surface_cells = algorithm.get_domain_surface_cells(data, mask, areas)
