"""
services/road_network.py — Download, cache, and query the Ahmedabad road graph.
Enhanced with KDTree for fast spatial lookups.
"""

import os
import numpy as np
import osmnx as ox
import networkx as nx
from scipy.spatial import cKDTree
from config import GRAPH_CACHE_FILE, BBOX, NETWORK_TYPE


def get_graph():
    """
    Return the central Ahmedabad driving network as a NetworkX MultiDiGraph.
    Downloads a bounding-box extract from OSM on first call; caches afterwards.
    """
    if os.path.exists(GRAPH_CACHE_FILE):
        G = ox.load_graphml(GRAPH_CACHE_FILE)
    else:
        G = ox.graph_from_bbox(bbox=BBOX, network_type=NETWORK_TYPE)
        ox.save_graphml(G, GRAPH_CACHE_FILE)
    return G


# ── KDTree-based spatial index ────────────────────────────────

_node_tree_cache = {}
_edge_tree_cache = {}


def _build_node_tree(G):
    """Build a KDTree over all graph nodes for fast nearest-node lookups."""
    graph_id = id(G)
    if graph_id in _node_tree_cache:
        return _node_tree_cache[graph_id]

    nodes = list(G.nodes(data=True))
    node_ids = [n for n, _ in nodes]
    coords = np.array([[d["y"], d["x"]] for _, d in nodes])
    tree = cKDTree(coords)

    result = (tree, node_ids, coords)
    _node_tree_cache[graph_id] = result
    return result


def _build_edge_tree(G):
    """Build a KDTree over edge midpoints for fast nearest-edge lookups."""
    graph_id = id(G)
    if graph_id in _edge_tree_cache:
        return _edge_tree_cache[graph_id]

    edges = list(G.edges(keys=True, data=True))
    edge_keys = [(u, v, k) for u, v, k, _ in edges]
    midpoints = []
    for u, v, k, _ in edges:
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        midpoints.append([
            (u_data["y"] + v_data["y"]) / 2,
            (u_data["x"] + v_data["x"]) / 2,
        ])
    midpoints = np.array(midpoints)
    tree = cKDTree(midpoints)

    result = (tree, edge_keys, midpoints)
    _edge_tree_cache[graph_id] = result
    return result


def snap_to_nearest_node(G, lat, lng):
    """Return the OSM node ID closest to (lat, lng) using KDTree — O(log n)."""
    tree, node_ids, _ = _build_node_tree(G)
    _, idx = tree.query([lat, lng])
    return node_ids[idx]


def get_nearest_edge(G, lat, lng):
    """Return (u, v, key) of the edge closest to (lat, lng) using KDTree."""
    tree, edge_keys, _ = _build_edge_tree(G)
    _, idx = tree.query([lat, lng])
    return edge_keys[idx]


def get_nearby_edges(G, lat, lng, radius_deg=0.002):
    """Return all (u, v, key) edges within radius_deg of (lat, lng).

    Default radius ~220m (0.002 degrees). Ensures the crash zone
    blocks all edges in the vicinity, not just the single nearest.
    """
    tree, edge_keys, _ = _build_edge_tree(G)
    indices = tree.query_ball_point([lat, lng], r=radius_deg)
    return [edge_keys[i] for i in indices]


def get_edge_nodes(G, lat, lng):
    """Given a crash location, return the two endpoint node IDs + edge key."""
    u, v, key = get_nearest_edge(G, lat, lng)
    return u, v, key


def get_node_coords(G, node_id):
    """Return (lat, lng) for a graph node."""
    node_data = G.nodes[node_id]
    return node_data["y"], node_data["x"]


def get_route_coords(G, route_nodes):
    """Convert a list of node IDs into (lat, lng) tuples.

    Uses edge geometry (LineString) when available for smooth curved roads,
    falling back to straight node-to-node lines when geometry is absent.
    """
    coords = []
    for i in range(len(route_nodes) - 1):
        u, v = route_nodes[i], route_nodes[i + 1]

        # Try to get edge geometry (curved road shape)
        geom = None
        if G.has_edge(u, v):
            edge_data = G.edges[u, v, 0] if hasattr(G, 'edge_key_dict_factory') else G.edges[u, v]
            geom = edge_data.get("geometry")

        if geom is not None:
            # geometry is a shapely LineString with (lng, lat) coords
            edge_coords = [(lat, lng) for lng, lat in geom.coords]
            # Check if geometry direction matches our route direction
            u_lat, u_lng = get_node_coords(G, u)
            first_lat, first_lng = edge_coords[0]
            if abs(first_lat - u_lat) + abs(first_lng - u_lng) > 0.0001:
                edge_coords = list(reversed(edge_coords))
            # Skip first point if it duplicates the previous segment's last point
            if coords and edge_coords:
                edge_coords = edge_coords[1:]
            coords.extend(edge_coords)
        else:
            # No geometry — use straight line between nodes
            lat, lng = get_node_coords(G, u)
            if not coords:
                coords.append((lat, lng))
            lat2, lng2 = get_node_coords(G, v)
            coords.append((lat2, lng2))

    # Ensure at least the last node is included
    if route_nodes and not coords:
        lat, lng = get_node_coords(G, route_nodes[0])
        coords.append((lat, lng))

    return coords


def get_street_name(G, u, v, key=0):
    """Return the street name for an edge, or 'Unnamed Road' if absent."""
    edge_data = G.edges[u, v, key]
    name = edge_data.get("name", "Unnamed Road")
    if isinstance(name, list):
        name = " / ".join(name)
    return name
