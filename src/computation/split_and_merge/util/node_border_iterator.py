import itertools as it

def iterate_node_border(node, func):
    node_x, node_y, node_z = node[0]
    node_w, node_h, node_d = node[1]
    
    border_points =      [(x,             node_y-1,      z            ) for x in range(node_x,   node_x+node_w+1) for z in range(node_z,   node_z+node_d+1)]
    border_points.extend([(x,             node_y+node_h, z            ) for x in range(node_x,   node_x+node_w+1) for z in range(node_z,   node_z+node_d+1)])
    border_points.extend([(node_x-1,      y,             z            ) for y in range(node_y-1, node_y+node_h+1) for z in range(node_z-1, node_z+node_d+1)])
    border_points.extend([(node_x+node_w, y,             z            ) for y in range(node_y,   node_y+node_h)   for z in range(node_z,   node_z+node_d+1)])
    border_points.extend([(x,             y,             node_z-1     ) for x in range(node_x,   node_x+node_w+1) for y in range(node_y-1, node_y+node_h+1)])
    border_points.extend([(x,             y,             node_z+node_d) for x in range(node_x,   node_x+node_w)   for y in range(node_y,   node_y+node_h)  ])
    
    for border_x, border_y, border_z in border_points:
        func(border_x, border_y, border_z)
        

def iterate_node_border_with_adjacent_node_cells(node, func):
    node_x, node_y, node_z = node[0]
    node_w, node_h, node_d = node[1]
    
    border_points =      [(x,             node_y-1,      z,             tuple(it.product(range(max(x-1, node_x), min(x+2, node_x+node_w)), [node_y],                                         range(max(z-1, node_z), min(z+2, node_z+node_d))))) for x in range(node_x,   node_x+node_w+1) for z in range(node_z,   node_z+node_d+1)]
    border_points.extend([(x,             node_y+node_h, z,             tuple(it.product(range(max(x-1, node_x), min(x+2, node_x+node_w)), [node_y+node_h-1],                                range(max(z-1, node_z), min(z+2, node_z+node_d))))) for x in range(node_x,   node_x+node_w+1) for z in range(node_z,   node_z+node_d+1)])
    border_points.extend([(node_x-1,      y,             z,             tuple(it.product([node_x],                                         range(max(y-1, node_y), min(y+2, node_y+node_h)), range(max(z-1, node_z), min(z+2, node_z+node_d))))) for y in range(node_y-1, node_y+node_h+1) for z in range(node_z-1, node_z+node_d+1)])
    border_points.extend([(node_x+node_w, y,             z,             tuple(it.product([node_x+node_w-1],                                range(max(y-1, node_y), min(y+2, node_y+node_h)), range(max(z-1, node_z), min(z+2, node_z+node_d))))) for y in range(node_y,   node_y+node_h)   for z in range(node_z,   node_z+node_d+1)])
    border_points.extend([(x,             y,             node_z-1,      tuple(it.product(range(max(x-1, node_x), min(x+2, node_x+node_w)), range(max(y-1, node_y), min(y+2, node_y+node_h)), [node_z])                                        )) for x in range(node_x,   node_x+node_w+1) for y in range(node_y-1, node_y+node_h+1)])
    border_points.extend([(x,             y,             node_z+node_d, tuple(it.product(range(max(x-1, node_x), min(x+2, node_x+node_w)), range(max(y-1, node_y), min(y+2, node_y+node_h)), [node_z+node_d-1])                               )) for x in range(node_x,   node_x+node_w)   for y in range(node_y,   node_y+node_h)  ])
    
    for border_x, border_y, border_z, adjacent_node_cells in border_points:
        func(border_x, border_y, border_z, adjacent_node_cells)

