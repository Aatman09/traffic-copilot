"""
services/routing.py — Compute alternate routes between start and end points
that avoid crash location(s). Enhanced with ETA estimation.
"""

import networkx as nx
from services.road_network import snap_to_nearest_node, get_route_coords, get_street_name, get_nearest_edge


# Speed estimates in km/h by traffic density
SPEED_MAP = {
    "Light": 40,
    "Moderate": 25,
    "Heavy": 15,
    "Gridlock": 8,
}

MAX_ALTERNATE_ROUTES = 3


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


def estimate_eta(distance_m: float, traffic_density: str = "Moderate") -> float:
    """
    Estimate travel time in minutes given distance and traffic density.
    Returns rounded float.
    """
    speed_kmh = SPEED_MAP.get(traffic_density, 25)
    speed_ms = speed_kmh * 1000 / 3600  # convert to m/s
    time_seconds = distance_m / speed_ms if speed_ms > 0 else 0
    return round(time_seconds / 60, 1)


def compute_alternate_routes(G, start_lat, start_lng, end_lat, end_lng,
                              crash_lat, crash_lng,
                              traffic_density="Moderate",
                              extra_crash_points=None):
    """
    Compute up to 3 alternate routes from start→end that AVOID crash edges.

    Args:
        G: NetworkX MultiDiGraph of the road network
        start_lat, start_lng: Start location
        end_lat, end_lng: End location
        crash_lat, crash_lng: Primary crash location
        traffic_density: For ETA estimation
        extra_crash_points: Optional list of (lat, lng) tuples for multi-crash

    Returns: (routes_list, blocked_street_name)
    """
    src = snap_to_nearest_node(G, start_lat, start_lng)
    dst = snap_to_nearest_node(G, end_lat, end_lng)

    D = _to_digraph(G)

    # Remove the primary crashed edge
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

    # Remove edges for any additional crash points
    if extra_crash_points:
        for clat, clng in extra_crash_points:
            try:
                u2, v2, _ = get_nearest_edge(G, clat, clng)
                if D.has_edge(u2, v2):
                    D.remove_edge(u2, v2)
                if D.has_edge(v2, u2):
                    D.remove_edge(v2, u2)
            except Exception:
                pass

    # Find up to MAX_ALTERNATE_ROUTES shortest paths
    routes = []
    try:
        path_gen = nx.shortest_simple_paths(D, src, dst, weight="length")
        for i, path in enumerate(path_gen):
            if i >= MAX_ALTERNATE_ROUTES:
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
            eta = estimate_eta(total_dist, traffic_density)
            routes.append({
                "coords": coords,
                "nodes": path,
                "distance_m": round(total_dist),
                "street_summary": ", ".join(
                    sorted(street_names - {"Unnamed Road"})[:5]
                ) or "Local Roads",
                "rank": i + 1,
                "eta_minutes": eta,
            })
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        pass

    return routes, blocked_street
