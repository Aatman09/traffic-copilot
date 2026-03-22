"""
ui/user_styles.py — Light, commuter-focused CSS theme for user_app.py.
"""


def get_user_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', 'Google Sans', Roboto, sans-serif !important;
}

#MainMenu, footer { display: none !important; }
header[data-testid="stHeader"] {
    background: #fff !important;
    border-bottom: 1px solid #e8eaed;
    box-shadow: 0 1px 2px rgba(60,64,67,.08);
}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 100%;
}

/* Sidebar (route planner) */
section[data-testid="stSidebar"] {
    background: #fff !important;
    border-right: 1px solid #e8eaed;
    box-shadow: 2px 0 6px rgba(60,64,67,.1);
}

/* ── Title bar ──────────────────────────────────── */
.user-title-bar {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.25rem;
}
.user-title-bar h1 {
    font-size: 1.3rem;
    font-weight: 600;
    color: #202124;
    margin: 0;
}
.user-title-bar .subtitle {
    font-size: 0.78rem;
    color: #5f6368;
    margin-left: auto;
}

/* ── Incident card ──────────────────────────────── */
.inc-card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15);
    padding: 14px 16px;
    margin-bottom: 0.75rem;
    border-left: 4px solid #ea4335;
    cursor: default;
    transition: box-shadow 0.2s;
}
.inc-card:hover {
    box-shadow: 0 2px 6px rgba(60,64,67,.35), 0 6px 14px rgba(60,64,67,.2);
}
.inc-card .inc-street {
    font-size: 0.95rem;
    font-weight: 600;
    color: #202124;
}
.inc-card .inc-meta {
    font-size: 0.78rem;
    color: #5f6368;
    margin-top: 4px;
}
.inc-card .inc-sev {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 6px;
}
.sev-low      { background: #e6f4ea; color: #137333; }
.sev-medium   { background: #fef7e0; color: #b06000; }
.sev-high     { background: #fce8e6; color: #c5221f; }
.sev-critical { background: #f3e8fd; color: #7627bb; }

/* ── Route card ─────────────────────────────────── */
.user-route-card {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(60,64,67,.25);
    padding: 12px 14px;
    border-left: 4px solid;
    margin-bottom: 0.5rem;
}
.user-route-card .eta {
    font-size: 1.2rem;
    font-weight: 700;
    color: #202124;
}
.user-route-card .dist {
    font-size: 0.8rem;
    color: #5f6368;
}
.user-route-card .streets {
    font-size: 0.72rem;
    color: #9aa0a6;
    margin-top: 4px;
}
.route-best-badge {
    display: inline-block;
    background: #e6f4ea;
    color: #137333;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 10px;
    margin-bottom: 2px;
}

/* ── Map ────────────────────────────────────────── */
iframe[title="st_folium.st_folium"] {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15) !important;
}

/* ── Empty state ────────────────────────────────── */
.user-empty {
    text-align: center;
    padding: 2rem 1rem;
    color: #5f6368;
}
.user-empty .icon { font-size: 2.5rem; opacity: 0.4; }
.user-empty .msg { font-size: 0.9rem; font-weight: 500; margin-top: 0.5rem; }
.user-empty .hint { font-size: 0.78rem; color: #9aa0a6; margin-top: 0.25rem; }

/* ── Waypoint dots (sidebar) ────────────────────── */
.wp-panel {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(60,64,67,.3), 0 4px 8px rgba(60,64,67,.15);
    padding: 14px;
    margin-bottom: 0.75rem;
}
.wp-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
}
.wp-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}
.wp-dot-start { background: #34a853; }
.wp-dot-end   { background: #1a73e8; }
.wp-dot-empty { background: #dadce0; }
.wp-label {
    font-size: 0.72rem;
    color: #5f6368;
    text-transform: uppercase;
    font-weight: 600;
    min-width: 36px;
}
.wp-coord {
    font-size: 0.82rem;
    color: #202124;
    font-weight: 500;
}
.wp-placeholder {
    font-size: 0.82rem;
    color: #9aa0a6;
    font-style: italic;
}
.wp-line {
    width: 2px;
    height: 14px;
    background: #dadce0;
    margin-left: 5px;
}

/* ── Tabs ───────────────────────────────────────── */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    color: #5f6368 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #1a73e8 !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: #1a73e8 !important;
}
</style>
"""
