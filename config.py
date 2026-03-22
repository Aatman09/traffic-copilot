"""
Configuration constants for the Traffic Incident Co-Pilot.
"""

# ── Map Defaults ──────────────────────────────────────────────
AHMEDABAD_CENTER = (23.0225, 72.5714)
DEFAULT_ZOOM = 13

# ── Groq LLM ─────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Road Network ──────────────────────────────────────────────
GRAPH_CACHE_FILE = "ahmedabad_drive.graphml"
NETWORK_TYPE = "drive"

# Bounding box: small central Ahmedabad area (~5 km radius)
# OSMnx v2.0 format: (west, south, east, north)
BBOX = (72.54, 22.98, 72.62, 23.06)

# ── Google Maps Color Palette ────────────────────────────────
GM_BLUE = "#1a73e8"
GM_GREEN = "#34a853"
GM_RED = "#ea4335"
GM_AMBER = "#fbbc04"
GM_PURPLE = "#9334e6"
GM_ORANGE = "#e8710a"

# ── Route Colors (Google Maps style) ─────────────────────────
ROUTE_COLORS = [GM_BLUE, GM_GREEN, GM_PURPLE, GM_ORANGE, GM_RED]

# ── App Strings ───────────────────────────────────────────────
APP_TITLE = "Traffic Co-Pilot"
APP_ICON = "🚦"
