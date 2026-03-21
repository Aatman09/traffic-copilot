"""
ui/history_panel.py — Incident history using st.dataframe.
"""

import streamlit as st
import pandas as pd
from models.incident import IncidentLog


def render_history_panel():
    """Render expandable incident history section below the main content."""
    log = IncidentLog()
    records = log.load()

    if not records:
        return

    with st.expander(f"Incident History ({len(records)} records)", icon=":material/history:"):
        # Build dataframe from records
        rows = []
        for rec in reversed(records):
            inc = rec.get("incident", {})
            rows.append({
                "Time": rec.get("saved_at", "?"),
                "Street": inc.get("blocked_street", "Unknown"),
                "Summary": (rec.get("analysis_summary", "—") or "—")[:80],
                "Routes": rec.get("route_count", 0),
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if st.button("Clear History", icon=":material/delete:", key="clear_history"):
            log.clear()
            st.rerun()
