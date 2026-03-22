"""
services/routing.py — Compute alternate routes between start and end points
that avoid crash location(s). Uses edge-removal for truly diverse routes.
"""

import networkx as nx
from services.road_network import snap_to_nearest_node, get_route_coords, get_street_name, get_nearest_edge, get_nearby_edges


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
    """Estimate travel time in minutes given distance and traffic density."""
    speed_kmh = SPEED_MAP.get(traffic_density, 25)
    speed_ms = speed_kmh * 1000 / 3600
    time_seconds = distance_m / speed_ms if speed_ms > 0 else 0
    return round(time_seconds / 60, 1)


def _extract_route_info(G, D, path, rank, traffic_density):
    """Build a route dict from a node path, using original graph for true distances."""
    total_dist = 0
    street_names = set()
    for a, b in zip(path[:-1], path[1:]):
        # Use original graph for accurate distance
        if G.has_edge(a, b):
            edge_data = list(G[a][b].values())[0]
        else:
            edge_data = D.edges.get((a, b), {})
        total_dist += edge_data.get("length", 0)
        name = edge_data.get("name", "Unnamed Road")
        if isinstance(name, list):
            street_names.update(name)
        else:
            street_names.add(name)

    coords = get_route_coords(G, path)
    eta = estimate_eta(total_dist, traffic_density)
    return {
        "coords": coords,
        "nodes": path,
        "distance_m": round(total_dist),
        "street_summary": ", ".join(
            sorted(street_names - {"Unnamed Road"})[:5]
        ) or "Local Roads",
        "rank": rank,
        "eta_minutes": eta,
    }


def compute_alternate_routes(G, start_lat, start_lng, end_lat, end_lng,
                              crash_lat, crash_lng,
                              traffic_density="Moderate",
                              extra_crash_points=None):
    """
    Compute up to 3 diverse alternate routes from start→end that AVOID crash edges.

    Strategy: find shortest path, then remove a chunk of its edges to force the
    next path onto completely different streets. This guarantees visually distinct routes.

    Returns: (routes_list, blocked_street_name)
    """
    src = snap_to_nearest_node(G, start_lat, start_lng)
    dst = snap_to_nearest_node(G, end_lat, end_lng)

    D = _to_digraph(G)

    # Block all edges within ~200m of crash
    blocked_street = "Unknown Road"
    try:
        u, v, key = get_nearest_edge(G, crash_lat, crash_lng)
        blocked_street = get_street_name(G, u, v, key)

        nearby = get_nearby_edges(G, crash_lat, crash_lng, radius_deg=0.002)
        for eu, ev, _ in nearby:
            if D.has_edge(eu, ev):
                D.remove_edge(eu, ev)
            if D.has_edge(ev, eu):
                D.remove_edge(ev, eu)
    except Exception:
        pass

    # Remove edges for additional crash points
    if extra_crash_points:
        for clat, clng in extra_crash_points:
            try:
                for eu, ev, _ in get_nearby_edges(G, clat, clng, radius_deg=0.002):
                    if D.has_edge(eu, ev):
                        D.remove_edge(eu, ev)
                    if D.has_edge(ev, eu):
                        D.remove_edge(ev, eu)
            except Exception:
                pass

    routes = []

    for route_num in range(MAX_ALTERNATE_ROUTES):
        try:
            path = nx.shortest_path(D, src, dst, weight="length")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            break

        route = _extract_route_info(G, D, path, route_num + 1, traffic_density)
        routes.append(route)

        # Remove the middle 60% of edges from this path to force divergence.
        # Keep start/end edges so the graph stays connected near src/dst.
        edges = list(zip(path[:-1], path[1:]))
        n = len(edges)
        if n <= 2:
            # Very short path — remove all edges
            for a, b in edges:
                if D.has_edge(a, b):
                    D.remove_edge(a, b)
                if D.has_edge(b, a):
                    D.remove_edge(b, a)
        else:
            # Keep first 20% and last 20%, remove the middle 60%
            keep_start = max(1, n // 5)
            keep_end = max(1, n // 5)
            remove_from = keep_start
            remove_to = n - keep_end
            for a, b in edges[remove_from:remove_to]:
                if D.has_edge(a, b):
                    D.remove_edge(a, b)
                if D.has_edge(b, a):
                    D.remove_edge(b, a)

    return routes, blocked_street
