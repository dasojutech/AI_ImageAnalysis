import osmnx as ox

def load_roads(place_name):
    graph = ox.graph_from_place(place_name, network_type="drive")
    _, edges = ox.graph_to_gdfs(graph)
    return edges
