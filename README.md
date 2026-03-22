# Traffic Incident Co-Pilot

AI-powered traffic incident management system for Ahmedabad, India. Admins mark crash locations, get alternate routes, severity assessments, resource dispatch suggestions, and congestion predictions. Commuters get real-time safe routing that avoids active incidents.

## Architecture

```
                                   FastAPI Backend (port 8080)
                                  ┌──────────────────────────┐
   Admin App (Streamlit)          │  REST API + WebSocket     │         User App (React + Vite)
  ┌──────────────────────┐        │                          │        ┌──────────────────────┐
  │  Incident form       │──POST──│  /incidents              │        │  Leaflet map         │
  │  Folium map          │──POST──│  /incidents/{id}/resolve │──WS───│  Search + directions │
  │  AI analysis tabs    │        │  /routes/safe            │──GET──│  Live incident feed  │
  │  Route cards + chat  │        │  /ws/incidents           │        │  Safe route cards    │
  └──────────────────────┘        └──────────┬───────────────┘        └──────────────────────┘
                                             │
              ┌──────────────────────────────┬┴─────────────────────────────┐
              │                              │                              │
     services/routing.py          services/llm_agent.py           backend/database.py
     NetworkX pathfinding         Groq LLM (llama-3.3-70b)        SQLite (data/incidents.db)
     Crash zone avoidance         Severity, dispatch, alerts      Incident persistence
     Diverse route generation     Congestion prediction           JSON field storage
              │                              │                              │
     services/road_network.py     services/notifications.py       backend/crossroads.py
     OSMnx graph + KDTree         Twilio WhatsApp/SMS             Auto intersection detection
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- A [Groq API key](https://console.groq.com/) (free tier works)
- (Optional) Twilio credentials for WhatsApp/SMS notifications

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"

# Optional — only needed for WhatsApp/SMS notifications
TWILIO_ACCOUNT_SID = "AC..."
TWILIO_AUTH_TOKEN = "..."
TWILIO_PHONE_NUMBER = "+1..."
TWILIO_WHATSAPP_NUMBER = "+14155238886"
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Start all three services

Open three terminals:

**Terminal 1 — Backend** (required for both apps):
```bash
uvicorn backend.main:app --port 8080
```

**Terminal 2 — Admin App** (traffic management dashboard):
```bash
streamlit run app.py
```
Opens at `http://localhost:8501`

**Terminal 3 — User App** (commuter-facing safe navigation):
```bash
cd frontend
npm run dev
```
Opens at `http://localhost:5173`

## Apps

### Admin App (Streamlit) — Traffic Manager

The admin dashboard for traffic police and incident managers.

**How to use:**
1. Click the map to place **Start** (green), **End** (blue), and **Crash** (red) markers
2. Fill in incident details (vehicle type, lanes blocked, traffic, weather)
3. Click **Analyze Incident** — this runs:
   - Alternate route computation (3 diverse routes avoiding the crash zone)
   - AI severity assessment (1-10 scale)
   - Resource dispatch suggestions (ambulance, police, tow truck, etc.)
   - Signal retiming recommendations
   - Public alert drafts (VMS, radio, social media)
   - Congestion prediction
4. Use the **Chat** tab to ask follow-up questions about the incident
5. Use the **Notify** tab to send WhatsApp/SMS alerts
6. **Resolve** incidents from the History panel when cleared

All incidents created or resolved here are broadcast in real-time to the User App via WebSocket.

**Features:**
- Google Maps-inspired UI with SVG pin markers and pulsing crash indicator
- Three map tile layers: Map (Voyager), Satellite (Esri), Dark (CartoDB)
- KPI row: routes found, fastest ETA, shortest distance, severity badge
- 6-tab results panel: Signals, Resources, Alerts, Congestion, Notify, Chat
- Incident history with filtering, sorting, and one-click resolve

### User App (React) — Safe Commute

The commuter-facing app for real-time safe navigation.

**How to use:**
1. Search for a starting point and destination (autocomplete via Nominatim)
   - Or click the map to place start (A) and end (B) pins
2. Click **Find Safe Routes** — computes routes avoiding all active crash zones
3. Click any route card to highlight it on the map
4. Active incidents appear as pulsing red markers with impact zones

**Features:**
- Google Maps-style floating directions panel with search autocomplete
- Real-time incident feed via WebSocket (instant updates when admin creates/resolves)
- Polling fallback every 10 seconds for reliability
- 3 diverse routes with different street combinations
- Click to switch between routes — active route is highlighted, others are dimmed
- Crash impact zones (300m radius) shown around incident markers
- Layer control: Map, Satellite, Dark
- Fully animated: panel entrance, card stagger reveal, button feedback, live-dot pulse

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/incidents` | Create incident (broadcasts via WebSocket) |
| `GET` | `/incidents` | List incidents (`?status=active` for live map) |
| `GET` | `/incidents/{id}` | Get single incident |
| `POST` | `/incidents/{id}/analyze` | Run full AI analysis pipeline |
| `POST` | `/incidents/{id}/resolve` | Mark resolved (broadcasts via WebSocket) |
| `POST` | `/incidents/from-photo` | Create from crash photo (Vision LLM) |
| `GET` | `/routes/preview` | Direct route preview |
| `POST` | `/routes/safe` | Safe route avoiding all active crashes |
| `POST` | `/notify` | Send WhatsApp/SMS via Twilio |
| `POST` | `/chat` | Multi-turn chat about an incident |
| `WS` | `/ws/incidents` | Real-time incident feed |

## Project Structure

```
app.py                          # Streamlit admin app (composition root)
config.py                       # Constants: map center, bbox, Groq model, colors

backend/
  main.py                       # FastAPI app (REST + WebSocket)
  database.py                   # SQLite CRUD operations
  crossroads.py                 # Auto intersection detection from crash point

services/
  api_client.py                 # HTTP client for backend API
  road_network.py               # OSMnx graph, KDTree spatial index
  routing.py                    # NetworkX pathfinding, crash avoidance, diverse routes
  llm_agent.py                  # Groq LLM: analysis, severity, dispatch, congestion, vision
  notifications.py              # Twilio WhatsApp/SMS

ui/
  styles.py                     # Google Maps-inspired CSS theme
  sidebar.py                    # Waypoint panel, incident form
  map_view.py                   # Folium map with SVG pins, routes, impact zones
  results_panel.py              # Route cards, 6-tab detail panel, chat, notifications
  history_panel.py              # Active incidents list, history table, resolve button

frontend/                       # React user app
  src/
    App.jsx                     # Main layout: full-bleed map + floating panel
    App.css                     # Google Maps pixel-accurate CSS
    components/
      Map.jsx                   # Leaflet map with crash markers, routes, layers
      Sidebar.jsx               # Directions panel: search, route cards, incidents
      Icons.jsx                 # Material Design SVG icon set
    hooks/
      useIncidents.js           # WebSocket + polling for live incident feed
    services/
      api.js                    # REST client + Nominatim geocoding

models/
  incident.py                   # Dataclasses (legacy JSON persistence)

data/
  incidents.db                  # SQLite database
```

## Key Technical Details

### Diverse Route Generation

Routes are computed using edge-removal on the road graph. After finding each shortest path, the middle 60% of its edges are removed from the graph, forcing the next path onto completely different streets. This guarantees visually distinct routes rather than minor variations.

### Crash Zone Blocking

All edges within a ~200m radius of the crash point are blocked using KDTree spatial lookup (`query_ball_point`). This prevents routes from passing through the accident zone on any nearby road, not just the exact crash edge.

### Real-Time Sync

The admin and user apps stay synchronized through the FastAPI backend:
- Admin creates/resolves incidents via the backend API
- Backend broadcasts changes to all connected user apps via WebSocket
- User app also polls `GET /incidents?status=active` every 10 seconds as fallback

### Road Network

The Ahmedabad road graph is downloaded from OpenStreetMap via OSMnx on first run and cached as `ahmedabad_drive.graphml` (~10MB). Spatial lookups use scipy `cKDTree` for O(log n) nearest-node and nearest-edge queries.

## Running Tests

```bash
pytest tests/
pytest tests/test_routing.py -v
```

## Environment Variables

These can be set in `.streamlit/secrets.toml` or as environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM features |
| `TWILIO_ACCOUNT_SID` | No | Twilio account SID for notifications |
| `TWILIO_AUTH_TOKEN` | No | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | No | Twilio SMS sender number |
| `TWILIO_WHATSAPP_NUMBER` | No | Twilio WhatsApp sandbox number |
