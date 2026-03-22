"""
ui/user_map.py — Folium map for the commuter app.
Shows active incidents, user start/end, and rerouted paths.
"""

import folium
from folium.plugins import Fullscreen
import streamlit as st
from config import AHMEDABAD_CENTER, DEFAULT_ZOOM, ROUTE_COLORS, GM_GREEN, GM_BLUE, GM_RED

_VOYAGER = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
_CARTO_ATTR = '&copy; <a href="https://carto.com/">CARTO</a>'


def _pin_icon(color: str, label: str):
    return folium.DivIcon(
        html=f"""
        <div style="position:relative;width:28px;height:40px;">
            <svg width="28" height="40" viewBox="0 0 30 42" fill="none">
                <path d="M15 0C6.72 0 0 6.72 0 15C0 26.25 15 42 15 42C15 42 30 26.25 30 15C30 6.72 23.28 0 15 0Z" fill="{color}"/>
                <circle cx="15" cy="15" r="7" fill="white" fill-opacity="0.9"/>
            </svg>
            <div style="
                position:absolute;top:6px;left:0;width:28px;
                text-align:center;font-size:11px;font-weight:700;
                color:{color};line-height:16px;
            ">{label}</div>
        </div>
        """,
        icon_size=(28, 40),
        icon_anchor=(14, 40),
        popup_anchor=(0, -40),
    )


def _crash_marker_icon(severity_score=None):
    """Red pulse crash marker. Darker for higher severity."""
    alpha = "0.35" if (severity_score or 0) >= 7 else "0.2"
    return folium.DivIcon(
        html=f"""
        <style>
        @keyframes crash-pulse{{0%{{transform:scale(.6);opacity:.9}}100%{{transform:scale(2.8);opacity:0}}}}
        </style>
        <div style="position:relative;width:24px;height:24px;">
            <div style="
                position:absolute;top:0;left:0;width:24px;height:24px;border-radius:50%;
                background:rgba(234,67,53,{alpha});
                animation:crash-pulse 2s ease-out infinite;
            "></div>
            <div style="
                position:absolute;top:4px;left:4px;width:16px;height:16px;border-radius:50%;
                background:{GM_RED};border:2px solid #fff;z-index:2;
            "></div>
        </div>
        """,
        icon_size=(24, 24),
        icon_anchor=(12, 12),
    )


def build_user_map(active_incidents: list):
    """Build the commuter map with active crash markers and user route."""
    center = st.session_state.get("u_map_center") or list(AHMEDABAD_CENTER)
    zoom = st.session_state.get("u_map_zoom") or DEFAULT_ZOOM

    m = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)

    folium.TileLayer(tiles=_VOYAGER, attr=_CARTO_ATTR, name="Map", show=True).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", show=False,
    ).add_to(m)
    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    Fullscreen(position="topright").add_to(m)

    # Plot all active incidents
    for inc in active_incidents:
        sev = inc.get("severity_score")
        label = inc.get("severity_label", "")
        street = inc.get("blocked_street", "Unknown")
        tooltip = f"⚠️ {street} — {sev}/10 {label}" if sev else f"⚠️ {street}"

        folium.Marker(
            [inc["crash_lat"], inc["crash_lng"]],
            icon=_crash_marker_icon(sev),
            tooltip=tooltip,
        ).add_to(m)
        folium.Circle(
            [inc["crash_lat"], inc["crash_lng"]],
            radius=300, color=GM_RED, fill=True,
            fill_color=GM_RED, fill_opacity=0.06,
            weight=1, dash_array="6 4",
        ).add_to(m)

    # User start pin
    if st.session_state.get("u_start_lat") is not None:
        folium.Marker(
            [st.session_state.u_start_lat, st.session_state.u_start_lng],
            icon=_pin_icon(GM_GREEN, "A"),
            tooltip="Your start",
        ).add_to(m)

    # User end pin
    if st.session_state.get("u_end_lat") is not None:
        folium.Marker(
            [st.session_state.u_end_lat, st.session_state.u_end_lng],
            icon=_pin_icon(GM_BLUE, "B"),
            tooltip="Your destination",
        ).add_to(m)

    # Preview (direct) route
    preview = st.session_state.get("u_preview")
    if preview and not st.session_state.get("u_routes"):
        folium.PolyLine(
            locations=preview["coords"], color="#9aa0a6",
            weight=4, opacity=0.5, dash_array="10 6",
            tooltip=f"Direct — {preview['distance_m']}m, ~{preview.get('eta_minutes', '?')} min",
        ).add_to(m)

    # Rerouted alternate routes
    for i, route in enumerate(st.session_state.get("u_routes", [])):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        best = i == 0
        # Outline
        folium.PolyLine(
            locations=route["coords"], color="#202124",
            weight=8 if best else 6, opacity=0.3,
        ).add_to(m)
        # Fill
        folium.PolyLine(
            locations=route["coords"], color=color,
            weight=5 if best else 3.5,
            opacity=0.95 if best else 0.7,
            tooltip=f"Route {route['rank']} — {route['distance_m']}m ({route.get('eta_minutes', '?')} min)",
        ).add_to(m)

    return m


def handle_user_map_click(map_data):
    """Handle map clicks to set start → end for the user route."""
    if not map_data or not map_data.get("last_clicked"):
        return

    click_key = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
    if click_key == st.session_state.get("u_last_click"):
        return

    lat, lng = click_key
    st.session_state.u_last_click = click_key

    # Save viewport
    bounds = map_data.get("bounds")
    zoom = map_data.get("zoom")
    if bounds:
        sw = bounds.get("_southWest", {})
        ne = bounds.get("_northEast", {})
        if sw and ne:
            st.session_state.u_map_center = [
                (sw["lat"] + ne["lat"]) / 2,
                (sw["lng"] + ne["lng"]) / 2,
            ]
    if zoom is not None:
        st.session_state.u_map_zoom = zoom

    mode = st.session_state.u_click_mode

    if mode == "start":
        st.session_state.u_start_lat = lat
        st.session_state.u_start_lng = lng
        st.session_state.u_click_mode = "end"
        st.session_state.u_routes = []
        st.session_state.u_preview = None
        st.rerun()
    elif mode == "end":
        st.session_state.u_end_lat = lat
        st.session_state.u_end_lng = lng
        st.session_state.u_click_mode = "done"
        # Fetch direct route preview
        from services.api_client import preview_route
        try:
            st.session_state.u_preview = preview_route(
                st.session_state.u_start_lat, st.session_state.u_start_lng,
                lat, lng,
            )
        except Exception:
            st.session_state.u_preview = None
        st.rerun()
