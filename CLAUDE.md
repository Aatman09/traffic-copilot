# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Traffic Incident Co-Pilot — a Streamlit web app for managing traffic incidents in Ahmedabad, India. Users mark start/end/crash points on an interactive map, then get AI-powered alternate routes, severity assessment, resource dispatch suggestions, and congestion predictions via Groq LLM (llama-3.3-70b-versatile).

**Note:** This repo is in a directory called `mesa/` and contains the Mesa ABM framework as a git-tracked dependency, but the actual application code is the traffic co-pilot. The Mesa library files show as deleted in git status — this is expected.

## Commands

### Run the app
```bash
streamlit run app.py
```

### Run all tests
```bash
pytest tests/
```

### Run a single test file
```bash
pytest tests/test_models.py
pytest tests/test_routing.py
```

### Run a single test
```bash
pytest tests/test_routing.py::test_estimate_eta_heavy_traffic
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Architecture

```
app.py              ← Streamlit composition root; wires UI to services
config.py           ← Constants (map center, bbox, Groq model, route colors)

models/
  incident.py       ← Dataclasses: Incident, Route, IncidentLog (JSON persistence)

services/
  road_network.py   ← OSMnx graph download, GraphML cache, KDTree spatial index
  routing.py        ← NetworkX shortest paths avoiding crash edge, ETA estimation
  llm_agent.py      ← Groq API: analyze_incident, assess_severity, suggest_dispatch, predict_congestion

ui/
  styles.py         ← Centralized CSS (dark theme)
  sidebar.py        ← Session state init, incident form inputs
  map_view.py       ← Folium map with markers/routes/impact zone
  results_panel.py  ← 6-tab results display + multi-turn chat
  history_panel.py  ← Past incident log viewer
```

Root-level `llm_agent.py`, `road_network.py`, `routing.py` are legacy/deprecated — the `services/` versions are the active ones.

### Key data flow
1. `app.py` loads the road graph via `services/road_network.get_graph()` (cached with `@st.cache_resource`)
2. Map clicks set start → end → crash coordinates in `st.session_state`
3. "Analyze Incident" triggers: route computation → severity → dispatch → analysis → congestion (all sequential)
4. Results stored in session state, rendered by `ui/results_panel.py`
5. Incidents persisted to `data/incident_log.json` via `IncidentLog`

### Secrets
API keys live in `.streamlit/secrets.toml` (GROQ_API_KEY, TOMTOM_API_KEY). Never commit this file.

### Cached data
`ahmedabad_drive.graphml` (~10MB) is the cached OSMnx road network. Regenerated automatically if missing.
