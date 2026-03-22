"""
backend/crossroads.py — Auto-detect the two nearest crossroads (intersections)
surrounding a crash location on the road graph.

Given crash GPS → find nearest edge → walk both directions along the road
until hitting intersection nodes (degree > 2). Returns (start, end) as
(lat, lng) tuples representing the road segment containing the crash.
"""

import networkx as nx
from services.road_network import snap_to_nearest_node, get_nearest_edge, get_node_coords


def _is_intersection(G, node: int, min_degree: int = 3) -> bool:
    """A node is an intersection if it connects 3+ roads (degree >= min_degree)."""
    return G.degree(node) >= min_degree


def _walk_to_intersection(G, start_node: int, away_from: int, max_hops: int = 50):
    """
    Walk along the road from start_node, moving away from away_from,
    until we hit an intersection or run out of hops.
    Returns the intersection node ID.
    """
    current = start_node
    previous = away_from

    for _ in range(max_hops):
        if _is_intersection(G, current):
            return current

        # Get neighbors (both in and out for directed graph)
        neighbors = set(G.successors(current)) | set(G.predecessors(current))
        neighbors.discard(previous)

        if not neighbors:
            return current  # dead end

        # Pick the neighbor that continues along the same road
        # Prefer neighbors on the same named street
        current_edge_name = _get_edge_name(G, previous, current)
        best = None
        for n in neighbors:
            if _get_edge_name(G, current, n) == current_edge_name:
                best = n
                break
        if best is None:
            best = next(iter(neighbors))

        previous = current
        current = best

    return current


def _get_edge_name(G, u: int, v: int) -> str:
    """Get the street name for an edge, handling both directions."""
    if G.has_edge(u, v):
        data = G.edges[u, v, 0] if isinstance(G, nx.MultiDiGraph) else G.edges[u, v]
        name = data.get("name", "")
        if isinstance(name, list):
            return name[0] if name else ""
        return name or ""
    if G.has_edge(v, u):
        data = G.edges[v, u, 0] if isinstance(G, nx.MultiDiGraph) else G.edges[v, u]
        name = data.get("name", "")
        if isinstance(name, list):
            return name[0] if name else ""
        return name or ""
    return ""


def find_crossroads(G, crash_lat: float, crash_lng: float) -> tuple:
    """
    Given crash coordinates, find the two nearest intersections
    that bound the road segment where the crash occurred.

    Returns: ((start_lat, start_lng), (end_lat, end_lng))
    """
    # Find the edge where the crash is
    u, v, _ = get_nearest_edge(G, crash_lat, crash_lng)

    # Walk in both directions to find intersections
    intersection_a = _walk_to_intersection(G, u, v)
    intersection_b = _walk_to_intersection(G, v, u)

    # If both directions hit the same node, use the edge endpoints
    if intersection_a == intersection_b:
        intersection_a = u
        intersection_b = v

    start = get_node_coords(G, intersection_a)
    end = get_node_coords(G, intersection_b)

    return start, end
