"""
ui/styles.py — Google Maps-inspired CSS theme.
"""


def get_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ───────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', 'Google Sans', Roboto, 'Segoe UI', sans-serif !important;
}

/* Hide Streamlit chrome (keep toolbar for sidebar toggle) */
#MainMenu, footer { display: none !important; }
header[data-testid="stHeader"] {
    background: #fff !important;
    border-bottom: 1px solid #e8eaed;
    box-shadow: 0 1px 2px rgba(60,64,67,.08);
}

/* Sidebar = Google Maps left panel */
section[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #e8eaed;
    box-shadow: 2px 0 4px rgba(60,64,67,.08);
}
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    padding-top: 0;
}

/* Reduce top padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 1400px;
}

div[data-testid="stVerticalBlock"] > div { padding-top: 0; }

/* ── Top Title Bar ────────────────────────────────────── */
.gm-title-bar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
}
.gm-title-bar h1 {
    font-size: 1.35rem;
    font-weight: 600;
    color: #202124;
    margin: 0;
    letter-spacing: -0.01em;
}
.gm-title-bar .gm-subtitle {
    font-size: 0.8rem;
    color: #5f6368;
    margin-left: auto;
}

/* ── Waypoint Panel (Google Maps directions style) ──── */
.waypoint-panel {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15);
    padding: 16px 16px 12px 16px;
    margin-bottom: 0.75rem;
}
.waypoint-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0;
}
.waypoint-dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 2.5px solid #fff;
    box-shadow: 0 0 0 1.5px currentColor;
}
.waypoint-dot-start { background: #34a853; color: #34a853; }
.waypoint-dot-end   { background: #1a73e8; color: #1a73e8; }
.waypoint-dot-crash { background: #ea4335; color: #ea4335; }
.waypoint-dot-empty {
    background: #fff;
    border: 2.5px solid #dadce0 !important;
    box-shadow: none;
}
.waypoint-line {
    width: 2px;
    height: 16px;
    background: #dadce0;
    margin-left: 6px;
}
.waypoint-coords {
    font-size: 0.82rem;
    color: #202124;
    font-weight: 500;
}
.waypoint-placeholder {
    font-size: 0.82rem;
    color: #9aa0a6;
    font-style: italic;
}
.waypoint-label {
    font-size: 0.68rem;
    color: #5f6368;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
    min-width: 38px;
}

/* ── Map Container ────────────────────────────────────── */
iframe[title="st_folium.st_folium"] {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15) !important;
}

/* ── Map toolbar row ──────────────────────────────────── */
.map-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.4rem;
}

/* ── Route Cards ──────────────────────────────────────── */
.route-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(60,64,67,.3), 0 1px 3px rgba(60,64,67,.15);
    padding: 14px 16px;
    border-left: 4px solid;
    transition: box-shadow 0.2s;
    cursor: default;
}
.route-card:hover {
    box-shadow: 0 1px 3px rgba(60,64,67,.4), 0 4px 8px rgba(60,64,67,.2);
}
.route-card-eta {
    font-size: 1.3rem;
    font-weight: 700;
    color: #202124;
    line-height: 1.2;
}
.route-card-dist {
    font-size: 0.82rem;
    color: #5f6368;
    margin-top: 2px;
}
.route-card-streets {
    font-size: 0.75rem;
    color: #9aa0a6;
    margin-top: 6px;
    line-height: 1.35;
}
.route-badge {
    display: inline-block;
    background: #e6f4ea;
    color: #137333;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    margin-bottom: 4px;
}

/* ── Section Headers ──────────────────────────────────── */
.gm-section-header {
    font-size: 0.75rem;
    font-weight: 600;
    color: #5f6368;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 1rem 0 0.5rem 0;
    padding-bottom: 0.35rem;
    border-bottom: 1px solid #e8eaed;
}

/* ── KPI Row ──────────────────────────────────────────── */
.gm-kpi-row {
    display: flex;
    gap: 1rem;
    margin: 0.75rem 0;
}
.gm-kpi {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(60,64,67,.2);
    padding: 12px 18px;
    flex: 1;
    text-align: center;
}
.gm-kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #202124;
}
.gm-kpi-label {
    font-size: 0.72rem;
    color: #5f6368;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 2px;
}

/* ── Severity Badge ───────────────────────────────────── */
.sev-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}
.sev-low      { background: #e6f4ea; color: #137333; }
.sev-medium   { background: #fef7e0; color: #b06000; }
.sev-high     { background: #fce8e6; color: #c5221f; }
.sev-critical { background: #f3e8fd; color: #7627bb; }

/* ── Priority Pill ────────────────────────────────────── */
.priority-pill {
    display: inline-block; padding: 2px 10px;
    border-radius: 12px; font-size: 0.72rem; font-weight: 600;
}
.priority-Critical { background: #fce8e6; color: #c5221f; }
.priority-High     { background: #fce8e6; color: #c5221f; }
.priority-Medium   { background: #fef7e0; color: #b06000; }
.priority-Low      { background: #e6f4ea; color: #137333; }

/* ── Google-style Tabs ────────────────────────────────── */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: #5f6368 !important;
    letter-spacing: 0.01em;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1a73e8 !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: #1a73e8 !important;
}

/* ── Buttons ──────────────────────────────────────────── */
button[data-testid="stFormSubmitButton"] > div > p,
div.stButton > button[kind="primary"] {
    font-weight: 500 !important;
}

/* ── Info/Warning/Success boxes ────────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* ── Chat ─────────────────────────────────────────────── */
div[data-testid="stChatMessage"] {
    border-radius: 12px;
}

/* ── Empty State ──────────────────────────────────────── */
.gm-empty-state {
    text-align: center;
    padding: 2rem 1rem;
    color: #5f6368;
}
.gm-empty-state .icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}
.gm-empty-state .msg {
    font-size: 0.9rem;
    font-weight: 500;
}
.gm-empty-state .hint {
    font-size: 0.78rem;
    color: #9aa0a6;
    margin-top: 0.3rem;
}

/* ── Loading overlay ──────────────────────────────────── */
.gm-loading {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 20px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15);
    margin: 0.5rem 0;
}
.gm-loading .spinner {
    width: 20px; height: 20px;
    border: 3px solid #e8eaed;
    border-top-color: #1a73e8;
    border-radius: 50%;
    animation: gm-spin 0.8s linear infinite;
}
@keyframes gm-spin {
    to { transform: rotate(360deg); }
}
.gm-loading .text {
    font-size: 0.85rem;
    color: #202124;
    font-weight: 500;
}
</style>
"""
