"""
ui/results_panel.py — Google Maps-inspired route cards and detail tabs.
"""

import streamlit as st
import pandas as pd
from config import ROUTE_COLORS


def render_route_cards():
    """Google Maps-style horizontal route summary cards."""
    routes = st.session_state.routes
    if not routes:
        return

    sev = st.session_state.get("severity", {})

    # KPI row
    shortest = min(r["distance_m"] for r in routes)
    fastest = min(r.get("eta_minutes", 999) for r in routes)
    sev_score = sev.get("severity_score", "")
    sev_label = sev.get("severity_label", "")

    sev_class = "sev-low"
    if sev_score and isinstance(sev_score, (int, float)):
        if sev_score >= 8:
            sev_class = "sev-critical"
        elif sev_score >= 6:
            sev_class = "sev-high"
        elif sev_score >= 4:
            sev_class = "sev-medium"

    st.markdown(
        f'<div class="gm-kpi-row">'
        f'<div class="gm-kpi"><div class="gm-kpi-value">{len(routes)}</div><div class="gm-kpi-label">Routes</div></div>'
        f'<div class="gm-kpi"><div class="gm-kpi-value">{fastest} min</div><div class="gm-kpi-label">Fastest ETA</div></div>'
        f'<div class="gm-kpi"><div class="gm-kpi-value">{shortest} m</div><div class="gm-kpi-label">Shortest</div></div>'
        f'<div class="gm-kpi"><div class="gm-kpi-value"><span class="sev-badge {sev_class}">{sev_score}/10 {sev_label}</span></div><div class="gm-kpi-label">Severity</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Route cards
    cols = st.columns(min(len(routes), 4))
    for i, route in enumerate(routes):
        color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
        eta = route.get("eta_minutes", "?")
        dist = route["distance_m"]
        streets = route.get("street_summary", "Local Roads")

        with cols[i % len(cols)]:
            badge = '<div class="route-badge">Best route</div>' if i == 0 else ""
            st.markdown(
                f'<div class="route-card" style="border-left-color:{color};">'
                f'{badge}'
                f'<div class="route-card-eta">{eta} min</div>'
                f'<div class="route-card-dist">{dist} m</div>'
                f'<div class="route-card-streets">{streets}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_results_panel(all_set: bool):
    """Render detail tabs below route cards."""
    if st.session_state.routes:
        tab_signals, tab_resources, tab_alerts, tab_congestion, tab_notify, tab_chat = st.tabs(
            ["Signals", "Resources", "Alerts", "Congestion", "Notify", "Chat"])

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

    elif not all_set:
        pass # The instructions are in the sidebar waypoint panel, no need for large empty states.


def _render_signals_tab():
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
        st.warning(f"AI Error: {a['error']}")
    else:
        st.info("Signal data will appear after analysis.")


def _render_resources_tab():
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
        st.warning(f"AI Error: {a['error']}")
    else:
        st.info("Alert drafts will appear after analysis.")


def _render_congestion_tab():
    congestion = st.session_state.get("congestion")
    if congestion and isinstance(congestion, dict) and "affected_areas" in congestion:
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
    from services.notifications import send_whatsapp, send_sms

    default_msg = ""
    a = st.session_state.get("analysis")
    if a and isinstance(a, dict) and "public_alerts" in a:
        default_msg = a["public_alerts"].get("social_media", "")
    if not default_msg:
        default_msg = st.session_state.get("incident_context", "Traffic incident reported.")

    if not st.session_state.get("analysis"):
        st.info("Notifications available after analysis.")
        return

    with st.form("notify_form"):
        channel = st.radio("Channel", ["WhatsApp", "SMS", "Both"],
                           horizontal=True)
        recipients = st.text_area(
            "Recipient phone numbers",
            placeholder="+919876543210\n+919876543211",
            help="One number per line with country code",
            height=80,
        )
        message = st.text_area("Message", value=default_msg, height=120)
        send_btn = st.form_submit_button("Send", type="primary",
                                         icon=":material/send:", use_container_width=True)

    if send_btn:
        numbers = [n.strip() for n in recipients.strip().splitlines() if n.strip()]
        if not numbers:
            st.warning("Enter at least one phone number.")
            return
        if not message.strip():
            st.warning("Message cannot be empty.")
            return

        ch = {"WhatsApp": "whatsapp", "SMS": "sms", "Both": "both"}[channel]
        with st.spinner("Sending..."):
            try:
                results = []
                if ch in ("whatsapp", "both"):
                    results += [{"channel": "whatsapp", **r} for r in send_whatsapp(numbers, message)]
                if ch in ("sms", "both"):
                    results += [{"channel": "sms", **r} for r in send_sms(numbers, message)]
                for r in results:
                    if "error" in r:
                        st.error(f"{r.get('channel', '')} to {r.get('number', '?')}: {r['error']}")
                    else:
                        st.success(f"{r.get('channel', '')} to {r.get('number', '?')}: {r.get('status', 'sent')}")
            except Exception as e:
                st.error(f"Notification error: {e}")


def _render_chat_tab():
    a = st.session_state.analysis
    if not a or (isinstance(a, dict) and "error" in a):
        st.info("Chat available after successful analysis.")
        return

    incident_id = st.session_state.get("incident_id")
    if not incident_id:
        st.info("Chat available after analysis.")
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
            try:
                context = st.session_state.get("incident_context", "")
                reply = chat_query(st.session_state.chat_history[:-1], context, user_q)
            except Exception as e:
                reply = f"Error: {e}"
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()
