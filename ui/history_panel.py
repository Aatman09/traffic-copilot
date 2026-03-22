"""
ui/history_panel.py — Incident history from SQLite database (no backend required).
"""

import streamlit as st
import pandas as pd


def _get_db_records(status=None, limit=50):
    """Get incidents from database directly."""
    try:
        from backend.database import init_db, get_active_incidents, get_all_incidents
        init_db()
        if status == "active":
            return get_active_incidents()
        return get_all_incidents(limit)
    except Exception:
        return []


def _resolve(incident_id):
    """Resolve via backend API (broadcasts to user app), fallback to direct DB."""
    try:
        from services.api_client import resolve_incident
        resolve_incident(incident_id)
    except Exception:
        try:
            from backend.database import resolve_incident as db_resolve
            db_resolve(incident_id)
        except Exception:
            pass


def render_history_panel():
    records = _get_db_records(limit=50)
    active_records = _get_db_records(status="active")

    if not records and not active_records:
        st.caption("No incidents recorded yet.")
        return

    # Render active incidents with Resolve buttons
    st.markdown("### Active Incidents")
    if not active_records:
        st.success("No active incidents currently reported.")
    else:
        with st.expander("Filter Active Incidents", icon=":material/filter_list:"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                search_street = st.text_input("Street Name")
            with f_col2:
                min_sev = st.slider("Min Severity", 1, 10, 1)
            with f_col3:
                time_sort = st.selectbox("Sort by Time", ["Newest First", "Oldest First"])

        if time_sort == "Newest First":
            active_records.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
        else:
            active_records.sort(key=lambda x: str(x.get('created_at', '')), reverse=False)

        filtered = []
        for inc in active_records:
            if search_street and search_street.lower() not in str(inc.get("blocked_street", "")).lower():
                continue
            sev_score = inc.get("severity_score") or 0
            if sev_score < min_sev:
                continue
            filtered.append(inc)

        if not filtered:
            st.info("No active incidents match your filters.")

        for inc in filtered:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{inc.get('vehicle_type', 'Vehicle')} crash** — {inc.get('blocked_street', 'Unknown')}")
            with col2:
                if st.button("Details", key=f"details_{inc['id']}"):
                    st.session_state.incident_id = inc['id']
                    st.session_state.crash_lat = inc['crash_lat']
                    st.session_state.crash_lng = inc['crash_lng']
                    st.session_state.start_lat = inc.get('start_lat')
                    st.session_state.start_lng = inc.get('start_lng')
                    st.session_state.end_lat = inc.get('end_lat')
                    st.session_state.end_lng = inc.get('end_lng')
                    st.session_state.blocked_street = inc.get('blocked_street', 'Unknown')

                    st.session_state.severity = {
                        "severity_score": inc.get("severity_score"),
                        "severity_label": inc.get("severity_label")
                    }
                    st.session_state.routes = inc.get("routes") or []
                    st.session_state.analysis = inc.get("analysis") or {}
                    st.session_state.dispatch = inc.get("dispatch") or {}
                    st.session_state.congestion = inc.get("congestion") or {}
                    st.session_state.click_mode = "done"

                    st.session_state.incident_context = (
                        f"Crash on {st.session_state.blocked_street}. "
                        f"Vehicles: {inc.get('vehicle_type', 'Unknown')}. "
                        f"Severity: {st.session_state.severity.get('severity_score', '?')}/10. "
                        f"Traffic: {inc.get('traffic_density', 'Unknown')}. Weather: {inc.get('weather', 'Unknown')}. "
                        f"{len(st.session_state.routes or [])} alternate routes found."
                    )
                    st.rerun()
            with col3:
                if st.button("Resolve", key=f"resolve_{inc['id']}"):
                    _resolve(inc['id'])
                    st.success("Incident resolved.")
                    st.rerun()

    st.divider()
    st.markdown("### Incident History")

    if not records:
        st.caption("No incidents yet.")
        return

    rows = []
    for rec in records:
        sev = rec.get("severity_score", "")
        label = rec.get("severity_label", "")
        sev_str = f"{sev}/10 ({label})" if sev else "—"
        rows.append({
            "ID": rec.get("id", "?"),
            "Time": rec.get("created_at", "?"),
            "Street": rec.get("blocked_street", "Unknown"),
            "Severity": sev_str,
            "Status": rec.get("status", "?"),
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn(width="small"),
            "Status": st.column_config.TextColumn(width="small"),
        },
    )
