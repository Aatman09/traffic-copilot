"""
ui/sidebar.py — Google Maps-style left panel in Streamlit sidebar.
Waypoints, form, controls — all in the sidebar so the map stays visible.
"""

import streamlit as st
from config import AHMEDABAD_CENTER


DEFAULTS = {
    "start_lat": None, "start_lng": None,
    "end_lat": None, "end_lng": None,
    "crash_lat": None, "crash_lng": None,
    "click_mode": "start",
    "incident_id": None,
    "routes": [], "blocked_street": "",
    "analysis": None, "severity": None, "dispatch": None, "congestion": None,
    "traffic_summary": None,
    "chat_history": [], "incident_context": "",
    "last_processed_click": None,
    "preview_route": None,
    "dark_map": False,
    "map_center": None,
    "map_zoom": None,
}


def init_session_state():
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_sidebar():
    """Render the full sidebar panel. Returns (analyze_btn, all_set, form_data)."""
    with st.sidebar:
        # ── Waypoint display ──
        _render_waypoints()

        # ── Severity (after analysis) ──
        sev = st.session_state.get("severity")
        if sev and isinstance(sev, dict) and "severity_score" in sev:
            score = sev.get("severity_score", "?")
            label = sev.get("severity_label", "")
            sev_class = "sev-low"
            if isinstance(score, (int, float)):
                if score >= 8: sev_class = "sev-critical"
                elif score >= 6: sev_class = "sev-high"
                elif score >= 4: sev_class = "sev-medium"
            st.markdown(
                f'<div style="text-align:center;margin:0.5rem 0;">'
                f'<span class="sev-badge {sev_class}">{score}/10 {label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Incident form ──
        with st.form("incident_form"):
            st.markdown('<div class="gm-section-header">Incident Details</div>',
                        unsafe_allow_html=True)

            vehicle_type = st.selectbox("Vehicle type",
                ["Car", "Truck / Heavy Vehicle", "Two-Wheeler", "Bus", "Auto-Rickshaw", "Multi-Vehicle"])
            c1, c2 = st.columns(2)
            with c1:
                lanes_affected = st.select_slider("Lanes blocked",
                    options=[1, 2, 3, 4, "Full Road"], value=1)
            with c2:
                traffic_density = st.selectbox("Traffic",
                    ["Light", "Moderate", "Heavy", "Gridlock"], index=1)
            weather = st.selectbox("Weather",
                ["Clear", "Rain", "Fog", "Night (Low Visibility)"])
            notes = st.text_input("Notes", placeholder="e.g. Fuel spill, injuries...")

            all_set = (st.session_state.start_lat is not None and
                       st.session_state.end_lat is not None and
                       st.session_state.crash_lat is not None)

            analyze_btn = st.form_submit_button(
                "Analyze Incident", use_container_width=True,
                disabled=not all_set, type="primary")

        st.divider()

        # ── Map controls ──
        st.button("Reset All", use_container_width=True, on_click=_reset,
                  type="secondary", icon=":material/refresh:")

    form_data = {
        "vehicle_type": vehicle_type,
        "lanes_affected": str(lanes_affected),
        "traffic_density": traffic_density,
        "weather": weather,
        "notes": notes,
    }
    return analyze_btn, all_set, form_data


def _render_waypoints():
    """Google Maps-style connected-dot waypoint display."""
    points = [
        ("START", "start", st.session_state.start_lat, st.session_state.start_lng),
        ("END", "end", st.session_state.end_lat, st.session_state.end_lng),
        ("CRASH", "crash", st.session_state.crash_lat, st.session_state.crash_lng),
    ]
    mode = st.session_state.click_mode
    rows_html = ""

    for i, (label, key, lat, lng) in enumerate(points):
        dot_class = f"waypoint-dot-{key}" if lat is not None else "waypoint-dot-empty"
        if lat is not None:
            coord_html = f'<span class="waypoint-coords">{lat:.5f}, {lng:.5f}</span>'
        elif mode == key:
            coord_html = '<span class="waypoint-placeholder">Click map...</span>'
        else:
            coord_html = '<span class="waypoint-placeholder">Not set</span>'

        rows_html += f"""
        <div class="waypoint-row">
            <div class="waypoint-dot {dot_class}"></div>
            <span class="waypoint-label">{label}</span>
            {coord_html}
        </div>"""
        if i < len(points) - 1:
            rows_html += '<div class="waypoint-line"></div>'

    st.markdown(f'<div class="waypoint-panel">{rows_html}</div>', unsafe_allow_html=True)


def _recenter_map():
    """Set map center and zoom to fit all placed points."""
    lats, lngs = [], []
    for attr in ["start", "end", "crash"]:
        lat = st.session_state.get(f"{attr}_lat")
        lng = st.session_state.get(f"{attr}_lng")
        if lat is not None and lng is not None:
            lats.append(lat)
            lngs.append(lng)

    if lats:
        st.session_state.map_center = [
            (min(lats) + max(lats)) / 2,
            (min(lngs) + max(lngs)) / 2,
        ]
        # Estimate zoom from span
        lat_span = max(lats) - min(lats)
        lng_span = max(lngs) - min(lngs)
        span = max(lat_span, lng_span, 0.001)
        if span < 0.005:
            st.session_state.map_zoom = 17
        elif span < 0.01:
            st.session_state.map_zoom = 16
        elif span < 0.03:
            st.session_state.map_zoom = 15
        elif span < 0.06:
            st.session_state.map_zoom = 14
        else:
            st.session_state.map_zoom = 13
    else:
        st.session_state.map_center = list(AHMEDABAD_CENTER)
        st.session_state.map_zoom = 13


def _reset():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
