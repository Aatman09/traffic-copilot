"""
ui/sidebar.py — Sidebar: compact incident form, map settings, actions.
"""

import streamlit as st


DEFAULTS = {
    "start_lat": None, "start_lng": None,
    "end_lat": None, "end_lng": None,
    "crash_lat": None, "crash_lng": None,
    "click_mode": "start",
    "routes": [], "blocked_street": "",
    "analysis": None, "severity": None, "dispatch": None, "congestion": None,
    "traffic_summary": None,
    "chat_history": [], "incident_context": "",
    "last_processed_click": None,
    "preview_route": None,
    "dark_map": True,
    "map_center": None,
    "map_zoom": None,
}


def init_session_state():
    """Initialise all session state defaults."""
    for k, v in DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _point_label(name: str, lat, lng) -> str:
    """Format a compact coordinate string."""
    return f"{name}: {lat:.4f}, {lng:.4f}"


def render_sidebar():
    """Render the sidebar and return (analyze_btn, all_set, form_data)."""
    with st.sidebar:
        # ── Map points (compact) ──
        st.caption("MAP POINTS")
        pts = [
            ("Start", st.session_state.start_lat, st.session_state.start_lng, ":green[set]"),
            ("End", st.session_state.end_lat, st.session_state.end_lng, ":blue[set]"),
            ("Crash", st.session_state.crash_lat, st.session_state.crash_lng, ":red[set]"),
        ]
        for name, lat, lng, badge in pts:
            if lat is not None:
                st.markdown(f"{badge} **{name}** {lat:.4f}, {lng:.4f}")
            else:
                st.markdown(f":gray[{name} — click map]")

        # ── Severity (compact, only after analysis) ──
        sev = st.session_state.get("severity")
        if sev and isinstance(sev, dict) and "severity_score" in sev:
            score = sev.get("severity_score", "?")
            label = sev.get("severity_label", "Unknown")
            st.metric("Severity", f"{score}/10", label)

        st.divider()

        # ── Map settings ──
        st.toggle(
            "Dark map",
            value=st.session_state.dark_map,
            key="dark_map",
        )

        st.divider()

        # ── Incident form ──
        with st.form("incident_form"):
            vehicle_type = st.selectbox("Vehicle type",
                ["Car", "Truck / Heavy Vehicle", "Two-Wheeler", "Bus", "Auto-Rickshaw", "Multi-Vehicle"])
            lanes_affected = st.select_slider("Lanes blocked", options=[1, 2, 3, 4, "Full Road"], value=1)
            traffic_density = st.selectbox("Traffic density", ["Light", "Moderate", "Heavy", "Gridlock"])
            weather = st.selectbox("Weather", ["Clear", "Rain", "Fog", "Night (Low Visibility)"])
            notes = st.text_area("Notes", placeholder="e.g. Fuel spill, injuries...", height=60)

            all_set = (st.session_state.start_lat is not None and
                       st.session_state.end_lat is not None and
                       st.session_state.crash_lat is not None)

            analyze_btn = st.form_submit_button(
                "Analyze Incident", use_container_width=True,
                disabled=not all_set, type="primary")

            if not all_set:
                remaining = []
                if st.session_state.start_lat is None: remaining.append("Start")
                if st.session_state.end_lat is None: remaining.append("End")
                if st.session_state.crash_lat is None: remaining.append("Crash")
                st.caption(f"Set {', '.join(remaining)} on the map first.")

        st.button("Reset All", use_container_width=True, on_click=_reset)

    form_data = {
        "vehicle_type": vehicle_type,
        "lanes_affected": str(lanes_affected),
        "traffic_density": traffic_density,
        "weather": weather,
        "notes": notes,
    }

    return analyze_btn, all_set, form_data


def _reset():
    """Reset all session state to defaults."""
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
