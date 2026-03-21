"""
ui/map_view.py — Folium map builder with preview route and crash radius overlay.
"""

import folium
import streamlit as st
from config import AHMEDABAD_CENTER, DEFAULT_ZOOM, ROUTE_COLORS

PREVIEW_COLOR = "#94a3b8"  # muted gray for the direct route preview


def build_map():
    """Build and return a Folium map with markers, routes, and crash radius."""
    dark = st.session_state.get("dark_map", True)
    tiles = "CartoDB dark_matter" if dark else "CartoDB positron"

    # Restore last viewport, or fall back to defaults
    center = st.session_state.get("map_center") or list(AHMEDABAD_CENTER)
    zoom = st.session_state.get("map_zoom") or DEFAULT_ZOOM

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=tiles,
        control_scale=True,
    )

    # Start marker
    if st.session_state.start_lat is not None:
        folium.Marker(
            [st.session_state.start_lat, st.session_state.start_lng],
            popup="<b>🟢 START</b>",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(m)

    # End marker
    if st.session_state.end_lat is not None:
        folium.Marker(
            [st.session_state.end_lat, st.session_state.end_lng],
            popup="<b>🔵 END</b>",
            icon=folium.Icon(color="blue", icon="flag-checkered", prefix="fa"),
        ).add_to(m)

    # Crash marker + impact radius circle
    if st.session_state.crash_lat is not None:
        folium.Marker(
            [st.session_state.crash_lat, st.session_state.crash_lng],
            popup=f"<b>🚨 CRASH</b><br>{st.session_state.blocked_street}",
            icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
        ).add_to(m)

        # Impact radius circle (300m radius)
        folium.Circle(
            [st.session_state.crash_lat, st.session_state.crash_lng],
            radius=300,
            color="#EF4444",
            fill=True,
            fill_color="#EF4444",
            fill_opacity=0.1,
            weight=2,
            dash_array="5",
            popup="Impact Zone (~300m radius)",
        ).add_to(m)

    # Preview route (direct path before analysis)
    preview = st.session_state.get("preview_route")
    if preview and not st.session_state.routes:
        folium.PolyLine(
            locations=preview["coords"],
            color=PREVIEW_COLOR,
            weight=4,
            opacity=0.6,
            dash_array="8",
            tooltip=f"Direct route — {preview['distance_m']} m, ~{preview.get('eta_minutes', '?')} min",
        ).add_to(m)

    # Route polylines (after analysis)
    for i, route in enumerate(st.session_state.routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        folium.PolyLine(
            locations=route["coords"],
            color=color,
            weight=6 if i == 0 else 4,
            opacity=0.9 if i == 0 else 0.7,
            popup=folium.Popup(
                f"<b>Route {route['rank']}</b><br>"
                f"Distance: {route['distance_m']}m<br>"
                f"ETA: {route.get('eta_minutes', 'N/A')} min<br>"
                f"Via: {route['street_summary']}", max_width=300),
            tooltip=f"Route {route['rank']} — {route['distance_m']}m ({route.get('eta_minutes', '?')} min)",
        ).add_to(m)

    return m


def _compute_preview(G):
    """Compute a direct shortest-path preview between start and end."""
    import networkx as nx
    from services.road_network import snap_to_nearest_node, get_route_coords
    from services.routing import _to_digraph, estimate_eta

    src = snap_to_nearest_node(G, st.session_state.start_lat, st.session_state.start_lng)
    dst = snap_to_nearest_node(G, st.session_state.end_lat, st.session_state.end_lng)
    D = _to_digraph(G)

    try:
        path = nx.shortest_path(D, src, dst, weight="length")
        total_dist = sum(
            D.edges[a, b].get("length", 0) for a, b in zip(path[:-1], path[1:])
        )
        coords = get_route_coords(G, path)
        return {
            "coords": coords,
            "distance_m": round(total_dist),
            "eta_minutes": estimate_eta(total_dist),
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def _save_viewport(map_data):
    """Persist the map's current center and zoom so the next rerun restores them."""
    bounds = map_data.get("bounds")
    zoom = map_data.get("zoom")
    if bounds:
        # bounds is {"_southWest": {lat, lng}, "_northEast": {lat, lng}}
        sw = bounds.get("_southWest", {})
        ne = bounds.get("_northEast", {})
        if sw and ne:
            center_lat = (sw["lat"] + ne["lat"]) / 2
            center_lng = (sw["lng"] + ne["lng"]) / 2
            st.session_state.map_center = [center_lat, center_lng]
    if zoom is not None:
        st.session_state.map_zoom = zoom


def handle_map_click(map_data, G=None):
    """Process map clicks and update session state. G is needed for preview route."""
    if not map_data or not map_data.get("last_clicked"):
        return

    click_key = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
    if click_key == st.session_state.last_processed_click:
        return

    lat, lng = click_key
    st.session_state.last_processed_click = click_key

    # Save viewport only when we're about to rerun for a click
    _save_viewport(map_data)

    current_mode = st.session_state.click_mode

    if current_mode == "start":
        st.session_state.start_lat = lat
        st.session_state.start_lng = lng
        st.session_state.click_mode = "end"
        st.session_state.routes = []
        st.session_state.preview_route = None
        st.session_state.analysis = None
        st.rerun()
    elif current_mode == "end":
        st.session_state.end_lat = lat
        st.session_state.end_lng = lng
        st.session_state.click_mode = "crash"
        st.session_state.routes = []
        st.session_state.analysis = None
        if G is not None:
            st.session_state.preview_route = _compute_preview(G)
        st.rerun()
    elif current_mode == "crash":
        st.session_state.crash_lat = lat
        st.session_state.crash_lng = lng
        st.session_state.click_mode = "done"
        st.rerun()
