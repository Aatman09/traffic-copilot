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


def get_edge_nodes(G, lat, lng):
    """Given a crash location, return the two endpoint node IDs + edge key."""
    u, v, key = get_nearest_edge(G, lat, lng)
    return u, v, key


def get_node_coords(G, node_id):
    """Return (lat, lng) for a graph node."""
    node_data = G.nodes[node_id]
    return node_data["y"], node_data["x"]


def get_route_coords(G, route_nodes):
    """Convert a list of node IDs into (lat, lng) tuples for Folium."""
    coords = []
    for node in route_nodes:
        lat, lng = get_node_coords(G, node)
        coords.append((lat, lng))
    return coords


def get_street_name(G, u, v, key=0):
    """Return the street name for an edge, or 'Unnamed Road' if absent."""
    edge_data = G.edges[u, v, key]
    name = edge_data.get("name", "Unnamed Road")
    if isinstance(name, list):
        name = " / ".join(name)
    return name
