"""
road_network.py — Download, cache, and query the Ahmedabad road graph.
"""

import os
import osmnx as ox
import networkx as nx
from shapely.geometry import Point
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


def snap_to_nearest_node(G, lat, lng):
    """Return the OSM node ID closest to (lat, lng) using simple distance."""
    min_dist = float("inf")
    nearest = None
    for node, data in G.nodes(data=True):
        dy = data["y"] - lat
        dx = data["x"] - lng
        d = dy * dy + dx * dx
        if d < min_dist:
            min_dist = d
            nearest = node
    return nearest


def get_nearest_edge(G, lat, lng):
    """
    Return (u, v, key) of the edge closest to (lat, lng).
    Uses midpoint of the edge as a simple approximation.
    """
    min_dist = float("inf")
    best = None
    for u, v, key, data in G.edges(keys=True, data=True):
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        mid_y = (u_data["y"] + v_data["y"]) / 2
        mid_x = (u_data["x"] + v_data["x"]) / 2
        dy = mid_y - lat
        dx = mid_x - lng
        d = dy * dy + dx * dx
        if d < min_dist:
            min_dist = d
            best = (u, v, key)
    return best


def get_edge_nodes(G, lat, lng):
    """
    Given a crash location, return the two endpoint node IDs
    of the nearest road segment, plus the edge key.
    """
    u, v, key = get_nearest_edge(G, lat, lng)
    return u, v, key


def get_node_coords(G, node_id):
    """Return (lat, lng) for a graph node."""
    node_data = G.nodes[node_id]
    return node_data["y"], node_data["x"]


def get_route_coords(G, route_nodes):
    """
    Convert a list of node IDs into a list of (lat, lng) tuples
    for drawing on a Folium map.
    """
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
