"""
ui/styles.py — Minimal CSS finishing touches.
Streamlit-native components handle most styling; this covers only gaps.
"""


def get_css() -> str:
    return """
<style>
/* Tighten default Streamlit block spacing */
div[data-testid="stVerticalBlock"] > div { padding-top: 0; }

/* Step indicator row */
.step-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.step-pill {
    padding: 0.3rem 0.75rem; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600;
}
.step-done    { background: #166534; color: #bbf7d0; }
.step-active  { background: #1e40af; color: #93c5fd; }
.step-pending { background: #334155; color: #64748b; }

/* Route accent stripe */
.route-stripe {
    border-left: 4px solid; border-radius: 4px;
    padding: 0.5rem 0.75rem; margin-bottom: 0.5rem;
    background: rgba(255,255,255,0.03);
}

/* Priority labels */
.priority-pill {
    display: inline-block; padding: 0.15rem 0.5rem;
    border-radius: 4px; font-size: 0.75rem; font-weight: 600;
}
.priority-Critical { background: #7C3AED; color: white; }
.priority-High     { background: #EF4444; color: white; }
.priority-Medium   { background: #F59E0B; color: #1e293b; }
.priority-Low      { background: #22C55E; color: #1e293b; }
</style>
"""
