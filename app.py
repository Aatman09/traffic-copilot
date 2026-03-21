"""
app.py — Streamlit dashboard for the Traffic Incident Co-Pilot.
Slim composition root using `ui/` and `services/` packages.
"""

import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime

from config import APP_TITLE, APP_ICON
from ui.styles import get_css
from ui.sidebar import init_session_state, render_sidebar
from ui.map_view import build_map, handle_map_click
from ui.results_panel import render_results_panel
from ui.history_panel import render_history_panel

from models.incident import Incident, IncidentLog
from services.road_network import get_graph
from services.routing import compute_alternate_routes
from services.llm_agent import analyze_incident, assess_severity, suggest_dispatch, predict_congestion

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_css(), unsafe_allow_html=True)
init_session_state()

# ── Graph loading (cached) ────────────────────────────────────
@st.cache_resource(show_spinner="Downloading road network / building spatial index...")
def load_graph():
    return get_graph()

# ── Header ────────────────────────────────────────────────────
st.title("Traffic Incident Co-Pilot")
st.caption("Mark start, end, and crash points on the map — get AI-powered alternate routes and resource dispatch.")

# ── Step indicator ────────────────────────────────────────────
mode = st.session_state.click_mode
start_state = "done" if st.session_state.start_lat else ("active" if mode == "start" else "pending")
end_state = "done" if st.session_state.end_lat else ("active" if mode == "end" else "pending")
crash_state = "done" if st.session_state.crash_lat else ("active" if mode == "crash" else "pending")

st.markdown(
    f'<div class="step-row">'
    f'<span class="step-pill step-{start_state}">1 Start</span>'
    f'<span class="step-pill step-{end_state}">2 End</span>'
    f'<span class="step-pill step-{crash_state}">3 Crash</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── Layout: Sidebar, Map, Results ─────────────────────────────
analyze_btn, all_set, form_data = render_sidebar()
G = load_graph()

map_col, info_col = st.columns([3, 2], gap="medium")

with map_col:
    m = build_map()
    map_data = st_folium(m, width=None, height=520, returned_objects=["last_clicked"])
    handle_map_click(map_data, G=G)

# ── Analyze Action ────────────────────────────────────────────
if analyze_btn and all_set:

    with st.status("Analyzing incident...", expanded=True) as status:
        st.write("Computing alternate routes...")
        routes, blocked_street = compute_alternate_routes(
            G,
            st.session_state.start_lat, st.session_state.start_lng,
            st.session_state.end_lat, st.session_state.end_lng,
            st.session_state.crash_lat, st.session_state.crash_lng,
            traffic_density=form_data["traffic_density"]
        )
        st.session_state.routes = routes
        st.session_state.blocked_street = blocked_street or ""
        st.session_state.preview_route = None  # replace preview with analysis routes

        if routes:
            crash_details = {
                "start_location": f"{st.session_state.start_lat:.5f}, {st.session_state.start_lng:.5f}",
                "end_location": f"{st.session_state.end_lat:.5f}, {st.session_state.end_lng:.5f}",
                "crash_location": f"{st.session_state.crash_lat:.5f}, {st.session_state.crash_lng:.5f}",
                "blocked_street": blocked_street or "Unknown",
                "vehicle_type": form_data["vehicle_type"],
                "lanes_affected": form_data["lanes_affected"],
                "traffic_density": form_data["traffic_density"],
                "weather": form_data["weather"],
                "notes": form_data["notes"],
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

            st.write("Assessing severity...")
            sev = assess_severity(crash_details)
            st.session_state.severity = sev

            st.write("Suggesting resource dispatch...")
            st.session_state.dispatch = suggest_dispatch(crash_details, sev)

            st.write("Generating route and signal analysis...")
            analysis = analyze_incident(crash_details, routes, blocked_street or "Unknown")
            st.session_state.analysis = analysis

            st.write("Generating congestion advisory...")
            st.session_state.congestion = predict_congestion(crash_details, sev)

            # Build context for chat
            st.session_state.incident_context = (
                f"Crash on {blocked_street}. Vehicles: {form_data['vehicle_type']}. "
                f"Severity: {sev.get('severity_score', '?')}/10. "
                f"Traffic: {form_data['traffic_density']}. Weather: {form_data['weather']}. "
                f"{len(routes)} alternate routes found."
            )
            st.session_state.chat_history = []

            # Save to History
            inc = Incident(
                crash_lat=st.session_state.crash_lat, crash_lng=st.session_state.crash_lng,
                start_lat=st.session_state.start_lat, start_lng=st.session_state.start_lng,
                end_lat=st.session_state.end_lat, end_lng=st.session_state.end_lng,
                blocked_street=blocked_street or "Unknown",
                **form_data,
                severity_score=sev.get('severity_score'),
                severity_reason=sev.get('reason')
            )
            IncidentLog().save(inc, analysis, routes)
            status.update(label="Analysis complete", state="complete")
            st.rerun()
        else:
            status.update(label="No routes found", state="error")
            st.error("No alternate routes found. Try different points.")

# ── Render Results & History ──────────────────────────────────
with info_col:
    render_results_panel(all_set)

st.divider()
render_history_panel()
