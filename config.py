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

# ── Route Colors (up to 5 alternates) ────────────────────────
ROUTE_COLORS = ["#00C853", "#FF6D00", "#2979FF", "#AA00FF", "#FFD600"]
CRASH_MARKER_COLOR = "red"

# ── App Strings ───────────────────────────────────────────────
APP_TITLE = "🚦 Traffic Incident Co-Pilot — Ahmedabad"
APP_ICON = "🚦"
