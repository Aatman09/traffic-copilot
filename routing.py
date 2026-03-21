"""
routing.py — Compute alternate routes between a start and end point,
             that avoid the crash location.
"""

import networkx as nx
from road_network import snap_to_nearest_node, get_route_coords, get_street_name, get_nearest_edge


def _to_digraph(G):
    """Convert MultiDiGraph → simple DiGraph, keeping shortest edge per pair."""
    D = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        length = data.get("length", float("inf"))
        if D.has_edge(u, v):
            if length < D.edges[u, v].get("length", float("inf")):
                D.edges[u, v].update(data)
        else:
            D.add_edge(u, v, **data)
    for node, data in G.nodes(data=True):
        if node in D.nodes:
            D.nodes[node].update(data)
    return D


def compute_alternate_routes(G, start_lat, start_lng, end_lat, end_lng,
                              crash_lat, crash_lng):
    """
    Compute up to 2 alternate routes from start→end that AVOID the crash edge.
    The crash location is mandatory — the edge at that point is always removed.

    Returns: (routes_list, blocked_street_name)
    """
    src = snap_to_nearest_node(G, start_lat, start_lng)
    dst = snap_to_nearest_node(G, end_lat, end_lng)

    D = _to_digraph(G)

    # Remove the crashed edge (mandatory)
    blocked_street = "Unknown Road"
    try:
        u, v, key = get_nearest_edge(G, crash_lat, crash_lng)
        blocked_street = get_street_name(G, u, v, key)
        if D.has_edge(u, v):
            D.remove_edge(u, v)
        if D.has_edge(v, u):
            D.remove_edge(v, u)
    except Exception:
        pass

    # Find up to 2 shortest paths
    routes = []
    try:
        path_gen = nx.shortest_simple_paths(D, src, dst, weight="length")
        for i, path in enumerate(path_gen):
            if i >= 2:
                break
            total_dist = 0
            street_names = set()
            for a, b in zip(path[:-1], path[1:]):
                edge_data = D.edges[a, b]
                total_dist += edge_data.get("length", 0)
                name = edge_data.get("name", "Unnamed Road")
                if isinstance(name, list):
                    street_names.update(name)
                else:
                    street_names.add(name)

            coords = get_route_coords(G, path)
            routes.append({
                "coords": coords,
                "nodes": path,
                "distance_m": round(total_dist),
                "street_summary": ", ".join(
                    sorted(street_names - {"Unnamed Road"})[:5]
                ) or "Local Roads",
                "rank": i + 1,
            })
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass

    return routes, blocked_street
