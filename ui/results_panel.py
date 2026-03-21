"""
ui/results_panel.py — Results tabs using Streamlit-native components.
"""

import streamlit as st
import pandas as pd
from config import ROUTE_COLORS


def render_results_panel(all_set: bool):
    """Render the right-side results panel with all tabs."""

    if st.session_state.routes:
        _render_stats()

        tab_routes, tab_signals, tab_resources, tab_alerts, tab_congestion, tab_notify, tab_chat = st.tabs(
            ["Routes", "Signals", "Resources", "Alerts", "Congestion", "Notify", "Chat"])

        with tab_routes:
            _render_routes_tab()
        with tab_signals:
            _render_signals_tab()
        with tab_resources:
            _render_resources_tab()
        with tab_alerts:
            _render_alerts_tab()
        with tab_congestion:
            _render_congestion_tab()
        with tab_notify:
            _render_notify_tab()
        with tab_chat:
            _render_chat_tab()

    elif all_set:
        _render_ready_state()
    else:
        _render_waiting_state()


def _render_stats():
    """KPI row using st.metric."""
    routes = st.session_state.routes
    shortest = min(r["distance_m"] for r in routes)
    fastest_eta = min(r.get("eta_minutes", 999) for r in routes)

    c1, c2, c3 = st.columns(3)
    c1.metric("Routes Found", len(routes))
    c2.metric("Shortest", f"{shortest} m")
    c3.metric("Fastest ETA", f"{fastest_eta} min")


def _render_routes_tab():
    """Routes tab with color-coded cards."""
    for i, route in enumerate(st.session_state.routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        eta = route.get("eta_minutes", "N/A")
        st.markdown(
            f'<div class="route-stripe" style="border-left-color:{color};">'
            f'<strong style="color:{color};">Route {route["rank"]}</strong> '
            f'&mdash; {route["distance_m"]} m, ~{eta} min<br>'
            f'<small>{route["street_summary"]}</small></div>',
            unsafe_allow_html=True,
        )

    a = st.session_state.analysis
    if a and isinstance(a, dict) and "route_recommendations" in a:
        st.subheader("AI Recommendations", divider="blue")
        for rec in a["route_recommendations"]:
            with st.container(border=True):
                st.markdown(f"**{rec.get('route_description', '')}**")
                st.caption(
                    f"Redistribution: ~{rec.get('estimated_redistribution_pct', '?')}%  "
                    f"| {rec.get('notes', '')}"
                )


def _render_signals_tab():
    """Signal retiming as a dataframe."""
    a = st.session_state.analysis
    if a and isinstance(a, dict) and "signal_retiming" in a and a["signal_retiming"]:
        rows = []
        for s in a["signal_retiming"]:
            rows.append({
                "Intersection": s.get("intersection", "—"),
                "Current Phase": s.get("current_phase", "—"),
                "Recommended": s.get("recommended_phase", "—"),
                "Reason": s.get("reason", "—"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    elif a and isinstance(a, dict) and "error" in a:
        st.warning(f"Groq API: {a['error']}")
    else:
        st.info("Signal data will appear after analysis.")


def _render_resources_tab():
    """Resource dispatch suggestions."""
    dispatch = st.session_state.get("dispatch")
    if dispatch and isinstance(dispatch, dict) and "resources" in dispatch:
        for res in dispatch["resources"]:
            icon = res.get("icon", "")
            rtype = res.get("type", "Unknown")
            priority = res.get("priority", "Medium")
            count = res.get("count", 1)
            reason = res.get("reason", "")

            with st.container(border=True):
                left, right = st.columns([4, 1])
                left.markdown(f"{icon} **{rtype}** x{count}")
                left.caption(reason)
                right.markdown(
                    f'<span class="priority-pill priority-{priority}">{priority}</span>',
                    unsafe_allow_html=True,
                )

        coord_notes = dispatch.get("coordination_notes", "")
        if coord_notes:
            st.info(coord_notes, icon=":material/assignment:")
    elif dispatch and isinstance(dispatch, dict) and "error" in dispatch:
        st.warning(f"Dispatch AI: {dispatch['error']}")
    else:
        st.info("Resource dispatch info will appear after analysis.")


def _render_alerts_tab():
    """Public alerts tab."""
    a = st.session_state.analysis
    if a and isinstance(a, dict) and "public_alerts" in a:
        alerts = a["public_alerts"]
        for label, key, icon in [
            ("VMS Sign", "vms_text", ":material/tv:"),
            ("Radio", "radio_script", ":material/radio:"),
            ("Social Media", "social_media", ":material/share:"),
        ]:
            with st.expander(f"{label}", icon=icon):
                st.write(alerts.get(key, "—"))
    elif a and isinstance(a, dict) and "error" in a:
        st.warning(f"Groq API: {a['error']}")
    else:
        st.info("Alert drafts will appear after analysis.")


def _render_congestion_tab():
    """AI Congestion advisory tab."""
    congestion = st.session_state.get("congestion")

    if congestion and isinstance(congestion, dict) and "affected_areas" in congestion:
        st.subheader("AI Congestion Advisory", divider="orange")

        c1, c2, c3 = st.columns(3)
        c1.metric("Duration", f"{congestion.get('predicted_congestion_duration_minutes', '?')} min")
        c2.metric("Peak Window", congestion.get("peak_congestion_window", "N/A"))
        c3.metric("Level", congestion.get("congestion_level", "N/A"))

        advice = congestion.get("advice", "")
        if advice:
            st.info(advice)

        for area in congestion.get("affected_areas", []):
            with st.container(border=True):
                st.markdown(f"**{area.get('area', '')}**")
                st.caption(
                    f"Impact: {area.get('impact', '')}  \n"
                    f"Alternative: {area.get('alternative', '')}"
                )
    elif congestion and isinstance(congestion, dict) and "error" in congestion:
        st.warning(f"Congestion AI: {congestion['error']}")
    else:
        st.info("AI congestion prediction will appear after analysis.")


def _render_notify_tab():
    """SMS and WhatsApp notification tab."""
    from services.notifications import format_alert_message, send_sms, send_whatsapp

    # Build default message from current incident data
    crash_details = {
        "blocked_street": st.session_state.get("blocked_street", "Unknown"),
        "vehicle_type": "",
        "traffic_density": "",
        "time": "",
    }
    # Pull from incident context if available
    ctx = st.session_state.get("incident_context", "")
    if ctx:
        crash_details["vehicle_type"] = ctx.split("Vehicles: ")[-1].split(".")[0] if "Vehicles:" in ctx else ""
        crash_details["traffic_density"] = ctx.split("Traffic: ")[-1].split(".")[0] if "Traffic:" in ctx else ""

    sev = st.session_state.get("severity")
    routes = st.session_state.get("routes", [])
    default_msg = format_alert_message(crash_details, sev, routes)

    # Use the social media alert if available (more concise)
    a = st.session_state.get("analysis")
    if a and isinstance(a, dict) and "public_alerts" in a:
        social = a["public_alerts"].get("social_media", "")
        if social:
            default_msg = social

    st.subheader("Send Notifications", divider="gray")

    with st.form("notify_form"):
        channel = st.radio("Channel", ["SMS", "WhatsApp", "Both"], horizontal=True)
        recipients = st.text_area(
            "Recipient phone numbers",
            placeholder="+919876543210\n+919876543211",
            help="One number per line, E.164 format (e.g. +91...)",
            height=80,
        )
        message = st.text_area("Message", value=default_msg, height=150)
        send_btn = st.form_submit_button("Send", type="primary", icon=":material/send:")

    if send_btn:
        numbers = [n.strip() for n in recipients.strip().splitlines() if n.strip()]
        if not numbers:
            st.warning("Enter at least one phone number.")
            return
        if not message.strip():
            st.warning("Message cannot be empty.")
            return

        results = []
        with st.spinner("Sending..."):
            if channel in ("SMS", "Both"):
                results += [("SMS", r) for r in send_sms(numbers, message)]
            if channel in ("WhatsApp", "Both"):
                results += [("WhatsApp", r) for r in send_whatsapp(numbers, message)]

        # Show results
        for ch, r in results:
            if "error" in r:
                st.error(f"{ch} to {r['number']}: {r['error']}")
            else:
                st.success(f"{ch} to {r['number']}: {r['status']}")


def _render_chat_tab():
    """Multi-turn chat using st.chat_message."""
    a = st.session_state.analysis
    if not a or (isinstance(a, dict) and "error" in a):
        st.info("Chat available after successful analysis.")
        return

    for msg in st.session_state.chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg["content"])

    user_q = st.chat_input("Ask about the incident...")
    if user_q:
        st.session_state.chat_history.append({"role": "user", "content": user_q})
        with st.spinner("Thinking..."):
            from services.llm_agent import chat_query
            reply = chat_query(
                st.session_state.chat_history[:-1],
                st.session_state.incident_context, user_q)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()


def _render_ready_state():
    st.status("All points set — ready to analyze", state="complete")
    st.caption("Click **Analyze Incident** in the sidebar.")


def _render_waiting_state():
    labels = {"start": "Start", "end": "End", "crash": "Crash"}
    cur = labels.get(st.session_state.click_mode, "")
    st.status(f"Click the map to set **{cur}** point", state="running")
    st.caption("Set all 3 points (Start, End, Crash) then analyze.")
