#  import numpy as np
#
#  def calculate_domain_centers(atoms, combined_translation_vectors, domains):
#  atom_pos = np.array(atoms, dtype=np.int32)
#  combined_trans_vecs = np.vstack(([0, 0, 0], combined_translation_vectors))
#  centers_list = []
#
#  for domain_nodes in domains:
#  max_distance = -1
#  for node_pos, node_dim in domain_nodes:
#  node_pos = np.array(node_pos)
#  node_dim = np.array(node_dim)
#  for x in range(node_pos[0], node_pos[0] + node_dim[0]):
#  for y in range(node_pos[1], node_pos[1] + node_dim[1]):
#  for z in range(node_pos[2], node_pos[2] + node_dim[2]):
#  min_distance = np.iinfo(np.int32).max
#  for atom in atom_pos:
#  for trans_vec in combined_trans_vecs:
#  diff = np.array([x, y, z]) - atom + trans_vec
#  current_distance = np.sum(diff ** 2)
#  if current_distance < min_distance:
#  min_distance = current_distance
#  if min_distance > max_distance:
#  max_distance = min_distance
#  current_center = np.array([x, y, z])
#  centers_list.append(tuple(current_center))
#  return centers_list
#
