"""
user_app.py — Public-facing commuter dashboard.
Shows live incidents on an interactive map and provides rerouting.

Run alongside the backend:
  uvicorn backend.main:app --port 8000
  streamlit run user_app.py --server.port 8502
"""

import streamlit as st
from streamlit_folium import st_folium

from config import APP_ICON, ROUTE_COLORS
from ui.user_styles import get_user_css
from ui.user_map import build_user_map, handle_user_map_click
from services.api_client import list_incidents, preview_route

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Traffic Co-Pilot — Commuter",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_user_css(), unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────
_defaults = {
    "u_start_lat": None, "u_start_lng": None,
    "u_end_lat": None, "u_end_lng": None,
    "u_click_mode": "start",
    "u_routes": [],
    "u_preview": None,
    "u_last_click": None,
    "u_map_center": None,
    "u_map_zoom": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar: route planner ────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗺️ Route Planner")

    # Waypoint display
    _points = [
        ("FROM", "start", st.session_state.u_start_lat, st.session_state.u_start_lng),
        ("TO", "end", st.session_state.u_end_lat, st.session_state.u_end_lng),
    ]
    rows_html = ""
    for i, (label, key, lat, lng) in enumerate(_points):
        dot_cls = f"wp-dot-{key}" if lat is not None else "wp-dot-empty"
        if lat is not None:
            coord = f'<span class="wp-coord">{lat:.5f}, {lng:.5f}</span>'
        elif st.session_state.u_click_mode == key:
            coord = '<span class="wp-placeholder">Click map…</span>'
        else:
            coord = '<span class="wp-placeholder">Not set</span>'
        rows_html += f'<div class="wp-row"><div class="wp-dot {dot_cls}"></div><span class="wp-label">{label}</span>{coord}</div>'
        if i == 0:
            rows_html += '<div class="wp-line"></div>'
    st.markdown(f'<div class="wp-panel">{rows_html}</div>', unsafe_allow_html=True)

    # Preview info
    preview = st.session_state.u_preview
    if preview:
        st.caption(f"Direct route: {preview['distance_m']}m, ~{preview.get('eta_minutes', '?')} min")

    # Find routes button
    both_set = (st.session_state.u_start_lat is not None and
                st.session_state.u_end_lat is not None)

    find_btn = st.button("🔍 Find Safe Routes", disabled=not both_set,
                         use_container_width=True, type="primary")

    if st.button("Reset", use_container_width=True, icon=":material/refresh:"):
        for k, v in _defaults.items():
            st.session_state[k] = v
        st.rerun()

    st.divider()

    # Active incident list in sidebar
    st.markdown("### ⚠️ Active Incidents")

# ── Fetch active incidents ────────────────────────────────────
try:
    active_incidents = list_incidents(status="active")
except Exception:
    active_incidents = []

# Show incident cards in sidebar
with st.sidebar:
    if not active_incidents:
        st.caption("No active incidents right now ✅")
    for inc in active_incidents:
        sev = inc.get("severity_score")
        label = inc.get("severity_label", "")
        street = inc.get("blocked_street", "Unknown")

        sev_cls = "sev-low"
        if sev and isinstance(sev, (int, float)):
            if sev >= 8: sev_cls = "sev-critical"
            elif sev >= 6: sev_cls = "sev-high"
            elif sev >= 4: sev_cls = "sev-medium"

        sev_html = f'<span class="inc-sev {sev_cls}">{sev}/10 {label}</span>' if sev else ""
        vehicle = inc.get("vehicle_type", "")
        time_str = inc.get("created_at", "")[:16]

        st.markdown(
            f'<div class="inc-card">'
            f'<div class="inc-street">🚨 {street}</div>'
            f'<div class="inc-meta">{vehicle} · {time_str}</div>'
            f'{sev_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Title ─────────────────────────────────────────────────────
st.markdown(
    '<div class="user-title-bar">'
    '<h1>🚦 Traffic Co-Pilot</h1>'
    '<span class="subtitle">Live incidents &amp; safe routing — Ahmedabad</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Map ───────────────────────────────────────────────────────
m = build_user_map(active_incidents)
map_data = st_folium(m, width=None, height=560, returned_objects=["last_clicked", "bounds", "zoom"])
handle_user_map_click(map_data)

# ── Find safe routes action ───────────────────────────────────
if find_btn and both_set:
    loading = st.empty()
    loading.info("⏳ Computing safe routes avoiding active incidents…")

    try:
        # For each active incident, request a reroute from the backend
        # Use the first active incident as the crash point (or fallback to direct)
        if active_incidents:
            from services.api_client import create_incident as api_create, analyze_incident as api_analyze

            # Create a temporary query incident to use the routing engine
            result_data = {
                "crash_lat": active_incidents[0]["crash_lat"],
                "crash_lng": active_incidents[0]["crash_lng"],
                "start_lat": st.session_state.u_start_lat,
                "start_lng": st.session_state.u_start_lng,
                "end_lat": st.session_state.u_end_lat,
                "end_lng": st.session_state.u_end_lng,
                "vehicle_type": "Car",
                "lanes_affected": str(active_incidents[0].get("lanes_affected", "1")),
                "traffic_density": active_incidents[0].get("traffic_density", "Moderate"),
                "weather": active_incidents[0].get("weather", "Clear"),
                "notes": "User route query",
            }
            inc_resp = api_create(result_data)
            inc_id = inc_resp["incident_id"]
            result = api_analyze(inc_id, result_data["traffic_density"])
            st.session_state.u_routes = result.get("routes", [])
        else:
            # No incidents — just show the direct route
            preview = preview_route(
                st.session_state.u_start_lat, st.session_state.u_start_lng,
                st.session_state.u_end_lat, st.session_state.u_end_lng,
            )
            if preview:
                st.session_state.u_routes = [{
                    **preview,
                    "rank": 1,
                    "street_summary": "Direct Route",
                }]

        loading.empty()
        st.rerun()
    except Exception as e:
        loading.empty()
        st.error(f"Routing error: {e}")
        st.caption("Make sure the backend is running: `uvicorn backend.main:app --port 8000`")


# ── Route results ─────────────────────────────────────────────
routes = st.session_state.get("u_routes", [])
if routes:
    st.markdown("### 🛣️ Safe Routes")
    cols = st.columns(min(len(routes), 4))
    for i, route in enumerate(routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        with cols[i % len(cols)]:
            badge = '<div class="route-best-badge">Fastest</div>' if i == 0 else ""
            st.markdown(
                f'<div class="user-route-card" style="border-left-color:{color};">'
                f'{badge}'
                f'<div class="eta">{route.get("eta_minutes", "?")} min</div>'
                f'<div class="dist">{route["distance_m"]} m</div>'
                f'<div class="streets">{route.get("street_summary", "")}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Show congestion advisory if available
    congestion = None
    try:
        if active_incidents:
            inc_detail = active_incidents[0]
            congestion_data = inc_detail.get("congestion")
            if congestion_data and isinstance(congestion_data, dict):
                congestion = congestion_data
    except Exception:
        pass

    if congestion and congestion.get("advice"):
        st.info(f"**Congestion Advisory:** {congestion['advice']}")

elif both_set and st.session_state.u_click_mode == "done":
    st.markdown(
        '<div class="user-empty">'
        '<div class="icon">✅</div>'
        '<div class="msg">Route set — click "Find Safe Routes"</div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    labels = {"start": "start (A)", "end": "destination (B)"}
    cur = labels.get(st.session_state.u_click_mode, "")
    st.markdown(
        f'<div class="user-empty">'
        f'<div class="icon">📍</div>'
        f'<div class="msg">Click the map to set your {cur}</div>'
        f'<div class="hint">Then click "Find Safe Routes" to get crash-avoiding directions</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
