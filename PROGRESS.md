# Traffic Incident Co-Pilot — Development Progress

## Architecture

```
Admin App (Streamlit)  ──→  FastAPI Backend  ←──  User App (React/Next.js - TODO)
         │                       │
         └── services/           ├── backend/database.py (SQLite)
             api_client.py       ├── backend/crossroads.py (auto-detect intersections)
                                 ├── backend/main.py (REST + WebSocket)
                                 │
                                 ├── services/road_network.py (OSMnx + KDTree)
                                 ├── services/routing.py (NetworkX pathfinding)
                                 ├── services/llm_agent.py (Groq LLM)
                                 └── services/notifications.py (Twilio WhatsApp/SMS)
```

## Completed Features

### 1. Core Streamlit Admin App
- Interactive Folium map with click-to-place markers (Start → End → Crash)
- Incident form: vehicle type, lanes, traffic density, weather, notes
- AI-powered analysis via Groq LLM (llama-3.3-70b-versatile):
  - Alternate route computation (up to 3 routes avoiding crash)
  - Severity assessment (1-10 scale)
  - Resource dispatch suggestions
  - Signal retiming recommendations
  - Public alert drafts (VMS, radio, social media)
  - Congestion prediction
- Multi-turn AI chat about the incident
- Incident history (persistent via SQLite)

### 2. Google Maps-Inspired UI Redesign
- Light theme with Google Material Design colors (#1a73e8, #34a853, #ea4335)
- Inter font family
- Sidebar as Google Maps-style left panel (waypoint dots, form, controls)
- Full-width map with SVG pin markers (teardrop shape)
- Pulsing red crash marker with animation
- Route cards with color stripes, ETA, distance, "Best route" badge
- KPI row (routes found, fastest ETA, shortest distance, severity badge)
- Layer control on map: Map (Voyager), Satellite (Esri), Dark (CartoDB)
- Google-style loading spinner during analysis
- Clean tabs, cards, and empty states

### 3. FastAPI Shared Backend
- **POST /incidents** — Create incident (auto-detects crossroads if start/end not provided)
- **POST /incidents/{id}/analyze** — Full AI analysis pipeline
- **GET /incidents** — List all incidents (with ?status=active filter)
- **GET /incidents/{id}** — Get single incident
- **POST /incidents/{id}/resolve** — Mark resolved
- **POST /notify** — Send WhatsApp/SMS via Twilio
- **POST /chat** — Multi-turn chat about an incident
- **GET /routes/preview** — Direct route preview
- **POST /incidents/from-photo** — Create from crash photo (Vision LLM)
- **WS /ws/incidents** — WebSocket for real-time incident broadcasting

### 4. Vision LLM (Crash Photo Analysis)
- Uses Groq llama-3.2-90b-vision-preview
- Extracts: vehicle type, count, severity, lanes blocked, weather, hazards
- Available via POST /incidents/from-photo endpoint

### 5. Auto Crossroad Detection
- `backend/crossroads.py` walks the road graph from crash edge to nearest intersections
- Identifies the road segment containing the crash (nodes with degree >= 3)
- Falls back to edge endpoints if no intersection found

### 6. Curved Road Rendering
- `get_route_coords()` uses OSMnx edge geometry (LineString) for smooth curves
- Falls back to straight node-to-node lines when geometry absent

### 7. Crash Zone Routing Fix
- `get_nearby_edges()` blocks ALL edges within ~200m radius of crash point
- Prevents routes from passing through the accident zone
- Fixes issue where single-edge blocking missed nearby parallel roads

### 8. Twilio Notifications
- WhatsApp via Twilio sandbox (+14155238886)
- SMS via Twilio
- Auto-strips spaces/dashes from phone numbers, adds + prefix
- Notification tab in admin app with channel selection

### 9. Admin App → API Wiring
- `services/api_client.py` — HTTP client for all backend endpoints
- Streamlit app no longer imports services directly
- Road graph only loaded by backend (not Streamlit)
- Preview routes via GET /routes/preview API

### 10. SQLite Database
- `data/incidents.db` — shared by admin + user apps
- JSON fields for analysis, routes, dispatch, congestion
- Status tracking (active/resolved)

## File Structure

```
app.py                          ← Streamlit composition root
config.py                       ← Constants, colors, Groq model

ui/
  styles.py                     ← Google Maps CSS theme
  sidebar.py                    ← Waypoint panel, incident form
  map_view.py                   ← Folium map, SVG pins, routes
  results_panel.py              ← Route cards, detail tabs, notify, chat
  history_panel.py              ← Incident history from API

services/
  api_client.py                 ← HTTP client for FastAPI backend
  road_network.py               ← OSMnx graph, KDTree spatial index
  routing.py                    ← NetworkX pathfinding, crash avoidance
  llm_agent.py                  ← Groq LLM integration
  notifications.py              ← Twilio WhatsApp/SMS

backend/
  __init__.py
  main.py                       ← FastAPI app (REST + WebSocket)
  database.py                   ← SQLite CRUD
  crossroads.py                 ← Auto intersection detection

models/
  incident.py                   ← Dataclasses (legacy JSON persistence)

data/
  incidents.db                  ← SQLite database
  incident_log.json             ← Legacy log (deprecated)

.streamlit/
  config.toml                   ← Light theme config
  secrets.toml                  ← API keys (GROQ, Twilio)
```

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend
uvicorn backend.main:app --port 8000

# Start the admin app (separate terminal)
streamlit run app.py
```

## TODO
- [ ] Build the user app (React/Next.js + MapLibre GL)
  - Live incident map via WebSocket
  - Route input and real-time rerouting
  - Mobile-friendly design
