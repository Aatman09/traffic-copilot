"""
ui/map_view.py — Folium map with Google Maps-style markers and routes.
"""

import folium
from folium.plugins import Fullscreen
import streamlit as st
from config import AHMEDABAD_CENTER, DEFAULT_ZOOM, ROUTE_COLORS, GM_GREEN, GM_BLUE, GM_RED

PREVIEW_COLOR = "#9aa0a6"

_VOYAGER = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
_CARTO_ATTR = '&copy; <a href="https://carto.com/">CARTO</a>'


def _pin_icon(color: str, label: str):
    """Google Maps-style pin marker."""
    return folium.DivIcon(
        html=f"""
        <div style="position:relative;width:30px;height:42px;">
            <svg width="30" height="42" viewBox="0 0 30 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 0C6.72 0 0 6.72 0 15C0 26.25 15 42 15 42C15 42 30 26.25 30 15C30 6.72 23.28 0 15 0Z" fill="{color}"/>
                <circle cx="15" cy="15" r="7" fill="white" fill-opacity="0.9"/>
            </svg>
            <div style="
                position:absolute; top:7px; left:0; width:30px;
                text-align:center; font-size:12px; font-weight:700;
                color:{color}; line-height:16px;
            ">{label}</div>
        </div>
        """,
        icon_size=(30, 42),
        icon_anchor=(15, 42),
        popup_anchor=(0, -42),
    )


def _crash_icon():
    """Pulsing red crash pin."""
    return folium.DivIcon(
        html=f"""
        <style>
        @keyframes gm-pulse{{
            0%{{transform:scale(.7);opacity:.8}}
            100%{{transform:scale(2.5);opacity:0}}
        }}
        </style>
        <div style="position:relative;width:30px;height:42px;">
            <div style="
                position:absolute; top:2px; left:2px;
                width:26px; height:26px; border-radius:50%;
                background:rgba(234,67,53,.3);
                animation:gm-pulse 1.8s ease-out infinite;
            "></div>
            <svg width="30" height="42" viewBox="0 0 30 42" fill="none" xmlns="http://www.w3.org/2000/svg" style="position:relative;z-index:2;">
                <path d="M15 0C6.72 0 0 6.72 0 15C0 26.25 15 42 15 42C15 42 30 26.25 30 15C30 6.72 23.28 0 15 0Z" fill="{GM_RED}"/>
                <circle cx="15" cy="15" r="7" fill="white" fill-opacity="0.9"/>
            </svg>
            <div style="
                position:absolute; top:7px; left:0; width:30px;
                text-align:center; font-size:14px; font-weight:700;
                color:{GM_RED}; line-height:16px; z-index:3;
            ">!</div>
        </div>
        """,
        icon_size=(30, 42),
        icon_anchor=(15, 42),
        popup_anchor=(0, -42),
    )


def build_map():
    """Build Folium map with Google Maps aesthetic."""
    center = st.session_state.get("map_center") or list(AHMEDABAD_CENTER)
    zoom = st.session_state.get("map_zoom") or DEFAULT_ZOOM

    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)

    # Tile layers — Map is default, others available via layer control
    folium.TileLayer(
        tiles=_VOYAGER, attr=_CARTO_ATTR, name="Map", show=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="CartoDB dark_matter", name="Dark", show=False,
    ).add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)

    Fullscreen(position="topright").add_to(m)

    # All active incidents — try API first, fallback to DB
    try:
        try:
            from services.api_client import list_incidents
            active_incidents = list_incidents(status="active")
        except Exception:
            from backend.database import init_db, get_active_incidents
            init_db()
            active_incidents = get_active_incidents()
        for inc in active_incidents:
            # Don't duplicate the one currently being created if they match exactly
            if st.session_state.crash_lat != inc["crash_lat"] or st.session_state.crash_lng != inc["crash_lng"]:
                folium.Marker(
                    [inc["crash_lat"], inc["crash_lng"]],
                    icon=_crash_icon(),
                    tooltip=f"Active Incident — {inc.get('blocked_street', 'Unknown')} ({inc.get('severity_score', '?')}/10)",
                ).add_to(m)
    except Exception:
        pass

    # Start pin
    if st.session_state.start_lat is not None:
        folium.Marker(
            [st.session_state.start_lat, st.session_state.start_lng],
            icon=_pin_icon(GM_GREEN, "S"),
            tooltip="Start Point",
        ).add_to(m)

    # End pin
    if st.session_state.end_lat is not None:
        folium.Marker(
            [st.session_state.end_lat, st.session_state.end_lng],
            icon=_pin_icon(GM_BLUE, "E"),
            tooltip="End Point",
        ).add_to(m)

    # Crash pin + impact zone
    if st.session_state.crash_lat is not None:
        folium.Marker(
            [st.session_state.crash_lat, st.session_state.crash_lng],
            icon=_crash_icon(),
            tooltip=f"Crash — {st.session_state.blocked_street}",
        ).add_to(m)
        folium.Circle(
            [st.session_state.crash_lat, st.session_state.crash_lng],
            radius=300, color=GM_RED, fill=True,
            fill_color=GM_RED, fill_opacity=0.06,
            weight=1, dash_array="6 4",
        ).add_to(m)

    # Preview route
    preview = st.session_state.get("preview_route")
    if preview and not st.session_state.routes:
        folium.PolyLine(
            locations=preview["coords"], color=PREVIEW_COLOR,
            weight=4, opacity=0.5, dash_array="10 6",
            tooltip=f"Direct — {preview['distance_m']} m, ~{preview.get('eta_minutes', '?')} min",
        ).add_to(m)

    # Analysis routes — outline + fill (Google Maps style)
    for i, route in enumerate(st.session_state.routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        best = i == 0

        # Dark outline
        folium.PolyLine(
            locations=route["coords"], color="#202124",
            weight=8 if best else 6, opacity=0.35,
        ).add_to(m)

        # Color fill
        folium.PolyLine(
            locations=route["coords"], color=color,
            weight=5 if best else 3.5,
            opacity=0.95 if best else 0.75,
            tooltip=f"Route {route['rank']} — {route['distance_m']} m ({route.get('eta_minutes', '?')} min)",
        ).add_to(m)

    return m


def compute_preview():
    """Compute a direct route preview using services directly."""
    import networkx as nx
    from services.road_network import get_graph, snap_to_nearest_node, get_route_coords
    from services.routing import _to_digraph, estimate_eta
    try:
        G = get_graph()
        src = snap_to_nearest_node(G, st.session_state.start_lat, st.session_state.start_lng)
        dst = snap_to_nearest_node(G, st.session_state.end_lat, st.session_state.end_lng)
        D = _to_digraph(G)
        path = nx.shortest_path(D, src, dst, weight="length")
        total_dist = sum(D.edges[a, b].get("length", 0) for a, b in zip(path[:-1], path[1:]))
        coords = get_route_coords(G, path)
        return {
            "coords": coords,
            "distance_m": round(total_dist),
            "eta_minutes": estimate_eta(total_dist),
        }
    except Exception:
        return None


def _save_viewport(map_data):
    bounds = map_data.get("bounds")
    zoom = map_data.get("zoom")
    if bounds:
        sw = bounds.get("_southWest", {})
        ne = bounds.get("_northEast", {})
        if sw and ne:
            st.session_state.map_center = [
                (sw["lat"] + ne["lat"]) / 2,
                (sw["lng"] + ne["lng"]) / 2,
            ]
    if zoom is not None:
        st.session_state.map_zoom = zoom


def handle_map_click(map_data):
    if not map_data or not map_data.get("last_clicked"):
        return

    click_key = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
    if click_key == st.session_state.last_processed_click:
        return

    lat, lng = click_key
    st.session_state.last_processed_click = click_key
    _save_viewport(map_data)

    mode = st.session_state.click_mode

    if mode == "start":
        st.session_state.start_lat = lat
        st.session_state.start_lng = lng
        st.session_state.click_mode = "end"
        st.session_state.routes = []
        st.session_state.preview_route = None
        st.session_state.analysis = None
        st.rerun()
    elif mode == "end":
        st.session_state.end_lat = lat
        st.session_state.end_lng = lng
        st.session_state.click_mode = "crash"
        st.session_state.routes = []
        st.session_state.analysis = None
        st.session_state.preview_route = compute_preview()
        st.rerun()
    elif mode == "crash" or mode == "done":
        st.session_state.crash_lat = lat
        st.session_state.crash_lng = lng
        st.session_state.click_mode = "done"
        st.rerun()
