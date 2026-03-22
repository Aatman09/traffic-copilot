"""
app.py — Traffic Incident Co-Pilot (Google Maps-inspired layout).
Sidebar = left panel, main area = map + results.

Create/resolve go through the backend API (so WebSocket broadcasts reach the user app).
Heavy AI analysis runs directly via services (no need to route through API).
"""

import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime

from config import APP_TITLE, APP_ICON
from ui.styles import get_css
from ui.sidebar import init_session_state, render_sidebar
from ui.map_view import build_map, handle_map_click
from ui.results_panel import render_route_cards, render_results_panel
from ui.history_panel import render_history_panel

from services.road_network import get_graph, get_nearest_edge, get_street_name
from services.routing import compute_alternate_routes
from services.llm_agent import analyze_incident, assess_severity, suggest_dispatch, predict_congestion
from services.api_client import create_incident as api_create, API_BASE

import requests

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
@st.cache_resource(show_spinner="Loading road network...")
def load_graph():
    return get_graph()

# ── Sidebar (Google Maps left panel) ─────────────────────────
analyze_btn, all_set, form_data = render_sidebar()

# ── Title ─────────────────────────────────────────────────────
st.markdown(
    '<div class="gm-title-bar">'
    '<h1>Traffic Co-Pilot</h1>'
    '<span class="gm-subtitle">AI-powered incident management &mdash; Ahmedabad</span>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Map (full-width) ─────────────────────────────────────────
m = build_map()
map_data = st_folium(m, width=None, height=550, returned_objects=["last_clicked"])
handle_map_click(map_data)

# ── Analyze Action ────────────────────────────────────────────
if analyze_btn and all_set:
    loading = st.empty()
    loading.markdown(
        '<div class="gm-loading">'
        '<div class="spinner"></div>'
        '<div class="text">Analyzing incident — computing routes & running AI...</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    try:
        G = load_graph()

        # Get blocked street name
        try:
            u, v, key = get_nearest_edge(G, st.session_state.crash_lat, st.session_state.crash_lng)
            blocked_street = get_street_name(G, u, v, key)
        except Exception:
            blocked_street = "Unknown Road"
        st.session_state.blocked_street = blocked_street

        # Create incident via backend API (triggers WebSocket broadcast to user app)
        try:
            inc_resp = api_create({
                "crash_lat": st.session_state.crash_lat,
                "crash_lng": st.session_state.crash_lng,
                "start_lat": st.session_state.start_lat,
                "start_lng": st.session_state.start_lng,
                "end_lat": st.session_state.end_lat,
                "end_lng": st.session_state.end_lng,
                "blocked_street": blocked_street,
                "vehicle_type": form_data["vehicle_type"],
                "lanes_affected": form_data["lanes_affected"],
                "traffic_density": form_data["traffic_density"],
                "weather": form_data["weather"],
                "notes": form_data["notes"],
            })
            incident_id = inc_resp["incident_id"]
        except Exception:
            # Fallback: save directly to DB if backend is down
            from backend.database import init_db, create_incident as db_create
            init_db()
            incident_id = db_create({
                "crash_lat": st.session_state.crash_lat,
                "crash_lng": st.session_state.crash_lng,
                "start_lat": st.session_state.start_lat,
                "start_lng": st.session_state.start_lng,
                "end_lat": st.session_state.end_lat,
                "end_lng": st.session_state.end_lng,
                "blocked_street": blocked_street,
                "vehicle_type": form_data["vehicle_type"],
                "lanes_affected": form_data["lanes_affected"],
                "traffic_density": form_data["traffic_density"],
                "weather": form_data["weather"],
                "notes": form_data["notes"],
            })
        st.session_state.incident_id = incident_id

        # Compute alternate routes (direct — heavy operation)
        routes, blocked = compute_alternate_routes(
            G,
            st.session_state.start_lat, st.session_state.start_lng,
            st.session_state.end_lat, st.session_state.end_lng,
            st.session_state.crash_lat, st.session_state.crash_lng,
            traffic_density=form_data["traffic_density"],
        )
        st.session_state.routes = routes

        # Build crash details for LLM
        crash_details = {
            "start_location": f"{st.session_state.start_lat:.5f}, {st.session_state.start_lng:.5f}",
            "end_location": f"{st.session_state.end_lat:.5f}, {st.session_state.end_lng:.5f}",
            "crash_location": f"{st.session_state.crash_lat:.5f}, {st.session_state.crash_lng:.5f}",
            "blocked_street": blocked or blocked_street,
            "vehicle_type": form_data["vehicle_type"],
            "lanes_affected": form_data["lanes_affected"],
            "traffic_density": form_data["traffic_density"],
            "weather": form_data["weather"],
            "notes": form_data["notes"],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        # AI calls (direct — heavy operations)
        sev = assess_severity(crash_details)
        dispatch = suggest_dispatch(crash_details, sev)
        analysis = analyze_incident(crash_details, routes, blocked or blocked_street)
        congestion = predict_congestion(crash_details, sev)

        st.session_state.severity = sev
        st.session_state.dispatch = dispatch
        st.session_state.analysis = analysis
        st.session_state.congestion = congestion
        st.session_state.preview_route = None

        # Update the DB with analysis results
        try:
            from backend.database import init_db, update_incident as db_update
            init_db()
            db_update(incident_id, {
                "routes": routes,
                "blocked_street": blocked or blocked_street,
                "severity_score": sev.get("severity_score"),
                "severity_label": sev.get("severity_label"),
                "analysis": analysis,
                "dispatch": dispatch,
                "congestion": congestion,
            })
        except Exception:
            pass

        loading.empty()

        sev_data = st.session_state.severity or {}
        if st.session_state.routes:
            st.session_state.incident_context = (
                f"Crash on {st.session_state.blocked_street}. "
                f"Vehicles: {form_data['vehicle_type']}. "
                f"Severity: {sev_data.get('severity_score', '?')}/10. "
                f"Traffic: {form_data['traffic_density']}. Weather: {form_data['weather']}. "
                f"{len(st.session_state.routes)} alternate routes found."
            )
        else:
            st.session_state.incident_context = (
                f"Crash on {st.session_state.blocked_street}. "
                f"Vehicles: {form_data['vehicle_type']}. "
                f"Severity: {sev_data.get('severity_score', '?')}/10. "
                f"Traffic: {form_data['traffic_density']}. Weather: {form_data['weather']}. "
                f"No alternate routes possible."
            )

        st.session_state.chat_history = []
        st.rerun()

    except Exception as e:
        loading.empty()
        st.error(f"Error: {e}")

# ── Route Cards + Details ─────────────────────────────────────
render_route_cards()
render_results_panel(all_set)

# ── History ───────────────────────────────────────────────────
with st.expander("History", icon=":material/history:", expanded=False):
    render_history_panel()
