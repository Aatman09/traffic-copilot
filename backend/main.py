"""
backend/main.py — FastAPI shared backend for admin + user apps.

Run: uvicorn backend.main:app --reload --port 8000
"""

import sys
import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to path so services/ can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.database import init_db, create_incident, get_incident, get_active_incidents, get_all_incidents, update_incident, resolve_incident
from services.road_network import get_graph
from services.routing import compute_alternate_routes
from services.llm_agent import analyze_incident, assess_severity, suggest_dispatch, predict_congestion, analyze_crash_photo, chat_query
from services.notifications import format_alert_message, send_whatsapp, send_sms

# ── App ───────────────────────────────────────────────────────
app = FastAPI(title="Traffic Incident Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB on startup
init_db()

# Load graph once
_graph = None
def _get_graph():
    global _graph
    if _graph is None:
        _graph = get_graph()
    return _graph


# ── WebSocket connection manager ─────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, message: dict):
        for ws in self.active[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.active.remove(ws)

manager = ConnectionManager()


# ── Pydantic models ──────────────────────────────────────────

class IncidentCreate(BaseModel):
    crash_lat: float
    crash_lng: float
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    vehicle_type: Optional[str] = "Unknown"
    lanes_affected: Optional[str] = "1"
    traffic_density: Optional[str] = "Moderate"
    weather: Optional[str] = "Clear"
    notes: Optional[str] = ""

class AnalyzeRequest(BaseModel):
    incident_id: int
    traffic_density: Optional[str] = "Moderate"

class NotifyRequest(BaseModel):
    incident_id: int
    channel: str  # "whatsapp", "sms", "both"
    phone_numbers: list[str]
    message: Optional[str] = None

class ChatRequest(BaseModel):
    incident_id: int
    conversation_history: list[dict] = []
    question: str


# ── Endpoints ────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "service": "Traffic Incident Co-Pilot API"}


@app.websocket("/ws/incidents")
async def ws_incidents(ws: WebSocket):
    """Real-time incident feed for user app."""
    await manager.connect(ws)
    try:
        # Send all active incidents on connect
        active = get_active_incidents()
        await ws.send_json({"type": "initial", "incidents": active})
        # Keep alive — listen for pings / client messages
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


@app.post("/incidents")
async def create_new_incident(incident: IncidentCreate):
    """Create a new incident from GPS/sensor data."""
    G = _get_graph()
    data = incident.model_dump()

    # Use provided start/end, or auto-detect crossroads from crash location
    if incident.start_lat is None or incident.end_lat is None:
        from backend.crossroads import find_crossroads
        start, end = find_crossroads(G, incident.crash_lat, incident.crash_lng)
        data["start_lat"] = start[0]
        data["start_lng"] = start[1]
        data["end_lat"] = end[0]
        data["end_lng"] = end[1]

    # Get blocked street name
    from services.road_network import get_nearest_edge, get_street_name
    try:
        u, v, key = get_nearest_edge(G, incident.crash_lat, incident.crash_lng)
        data["blocked_street"] = get_street_name(G, u, v, key)
    except Exception:
        data["blocked_street"] = "Unknown Road"

    incident_id = create_incident(data)

    # Broadcast to user app via WebSocket
    incident_data = get_incident(incident_id)
    await manager.broadcast({"type": "new_incident", "incident": incident_data})

    return {"incident_id": incident_id, **data}


@app.post("/incidents/{incident_id}/analyze")
async def analyze(incident_id: int, req: AnalyzeRequest = None):
    """Run full AI analysis on an incident."""
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    G = _get_graph()
    traffic_density = req.traffic_density if req else "Moderate"

    # Compute routes
    routes, blocked_street = compute_alternate_routes(
        G,
        inc["start_lat"], inc["start_lng"],
        inc["end_lat"], inc["end_lng"],
        inc["crash_lat"], inc["crash_lng"],
        traffic_density=traffic_density,
    )

    crash_details = {
        "start_location": f"{inc['start_lat']:.5f}, {inc['start_lng']:.5f}",
        "end_location": f"{inc['end_lat']:.5f}, {inc['end_lng']:.5f}",
        "crash_location": f"{inc['crash_lat']:.5f}, {inc['crash_lng']:.5f}",
        "blocked_street": blocked_street or inc.get("blocked_street", "Unknown"),
        "vehicle_type": inc.get("vehicle_type", "Unknown"),
        "lanes_affected": inc.get("lanes_affected", "1"),
        "traffic_density": traffic_density,
        "weather": inc.get("weather", "Clear"),
        "notes": inc.get("notes", ""),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # AI calls
    sev = assess_severity(crash_details)
    dispatch = suggest_dispatch(crash_details, sev)
    analysis = analyze_incident(crash_details, routes, blocked_street or "Unknown")
    congestion = predict_congestion(crash_details, sev)

    # Update DB
    update_data = {
        "routes": routes,
        "blocked_street": blocked_street or inc.get("blocked_street"),
        "severity_score": sev.get("severity_score"),
        "severity_label": sev.get("severity_label"),
        "analysis": analysis,
        "dispatch": dispatch,
        "congestion": congestion,
    }
    update_incident(incident_id, update_data)

    # Broadcast update
    updated = get_incident(incident_id)
    await manager.broadcast({"type": "incident_updated", "incident": updated})

    return {
        "incident_id": incident_id,
        "routes": routes,
        "severity": sev,
        "dispatch": dispatch,
        "analysis": analysis,
        "congestion": congestion,
    }


@app.get("/incidents")
def list_incidents(status: Optional[str] = None, limit: int = 50):
    """List incidents. ?status=active for live map."""
    if status == "active":
        return get_active_incidents()
    return get_all_incidents(limit)


@app.get("/incidents/{incident_id}")
def get_single_incident(incident_id: int):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc


@app.post("/incidents/{incident_id}/resolve")
async def resolve(incident_id: int):
    """Mark incident as resolved."""
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    resolve_incident(incident_id)
    await manager.broadcast({"type": "incident_resolved", "incident_id": incident_id})
    return {"status": "resolved"}


@app.post("/notify")
def notify(req: NotifyRequest):
    """Send WhatsApp/SMS notifications."""
    inc = get_incident(req.incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    message = req.message
    if not message:
        crash_details = {
            "blocked_street": inc.get("blocked_street", "Unknown"),
            "vehicle_type": inc.get("vehicle_type", "Unknown"),
            "traffic_density": inc.get("traffic_density", "Unknown"),
            "time": inc.get("created_at", ""),
        }
        sev = {"severity_score": inc.get("severity_score"),
               "severity_label": inc.get("severity_label")}
        message = format_alert_message(crash_details, sev, inc.get("routes"))

    results = []
    if req.channel in ("whatsapp", "both"):
        results += [{"channel": "whatsapp", **r} for r in send_whatsapp(req.phone_numbers, message)]
    if req.channel in ("sms", "both"):
        results += [{"channel": "sms", **r} for r in send_sms(req.phone_numbers, message)]

    return {"results": results}


@app.post("/incidents/from-photo")
async def create_from_photo(
    lat: float = Form(...),
    lng: float = Form(...),
    photo: UploadFile = File(...),
):
    """Create an incident from GPS coords + crash photo. Vision LLM extracts all details."""
    image_bytes = await photo.read()
    vision_result = analyze_crash_photo(image_bytes)

    if "error" in vision_result:
        raise HTTPException(status_code=422, detail=vision_result["error"])

    G = _get_graph()

    # Auto-detect crossroads
    from backend.crossroads import find_crossroads
    start, end = find_crossroads(G, lat, lng)

    # Get blocked street
    from services.road_network import get_nearest_edge, get_street_name
    try:
        u, v, key = get_nearest_edge(G, lat, lng)
        blocked_street = get_street_name(G, u, v, key)
    except Exception:
        blocked_street = "Unknown Road"

    data = {
        "crash_lat": lat,
        "crash_lng": lng,
        "start_lat": start[0],
        "start_lng": start[1],
        "end_lat": end[0],
        "end_lng": end[1],
        "blocked_street": blocked_street,
        "vehicle_type": vision_result.get("vehicle_type", "Unknown"),
        "lanes_affected": str(vision_result.get("lanes_blocked", "1")),
        "traffic_density": "Moderate",
        "weather": vision_result.get("weather_visible", "Clear"),
        "notes": vision_result.get("visible_damage", ""),
        "severity_score": vision_result.get("estimated_severity"),
        "severity_label": vision_result.get("severity_label"),
    }

    incident_id = create_incident(data)

    incident_data = get_incident(incident_id)
    await manager.broadcast({"type": "new_incident", "incident": incident_data})

    return {
        "incident_id": incident_id,
        "vision_analysis": vision_result,
        **data,
    }


@app.get("/routes/preview")
def preview_route(start_lat: float, start_lng: float, end_lat: float, end_lng: float):
    """Compute a direct route preview (no crash avoidance)."""
    import networkx as nx
    from services.road_network import snap_to_nearest_node, get_route_coords
    from services.routing import _to_digraph, estimate_eta

    G = _get_graph()
    src = snap_to_nearest_node(G, start_lat, start_lng)
    dst = snap_to_nearest_node(G, end_lat, end_lng)
    D = _to_digraph(G)

    try:
        path = nx.shortest_path(D, src, dst, weight="length")
        total_dist = sum(D.edges[a, b].get("length", 0) for a, b in zip(path[:-1], path[1:]))
        coords = get_route_coords(G, path)
        return {
            "coords": coords,
            "distance_m": round(total_dist),
            "eta_minutes": estimate_eta(total_dist),
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        raise HTTPException(status_code=404, detail="No route found")


class SafeRouteRequest(BaseModel):
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    traffic_density: Optional[str] = "Moderate"


@app.post("/routes/safe")
def safe_route(req: SafeRouteRequest):
    """Compute routes from start→end avoiding ALL active incident crash zones."""
    G = _get_graph()
    active = get_active_incidents()

    if not active:
        # No incidents — return direct route
        return preview_route(req.start_lat, req.start_lng, req.end_lat, req.end_lng)

    # Use the first active crash as primary, rest as extra
    primary = active[0]
    extra = [(inc["crash_lat"], inc["crash_lng"]) for inc in active[1:]]

    routes, blocked = compute_alternate_routes(
        G,
        req.start_lat, req.start_lng,
        req.end_lat, req.end_lng,
        primary["crash_lat"], primary["crash_lng"],
        traffic_density=req.traffic_density,
        extra_crash_points=extra,
    )

    # Count only incidents that are actually near the route corridor (~500m)
    import math
    avoided = 0
    for inc in active:
        clat, clng = inc["crash_lat"], inc["crash_lng"]
        near_route = False
        for route in routes:
            for coord in route.get("coords", []):
                dlat = clat - coord[0]
                dlng = clng - coord[1]
                if math.sqrt(dlat * dlat + dlng * dlng) < 0.005:  # ~500m
                    near_route = True
                    break
            if near_route:
                break
        if near_route:
            avoided += 1

    return {
        "routes": routes,
        "blocked_street": blocked,
        "crashes_avoided": avoided,
    }


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """Multi-turn chat about an incident."""
    inc = get_incident(req.incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    context = (
        f"Crash on {inc.get('blocked_street', 'Unknown')}. "
        f"Vehicle: {inc.get('vehicle_type', 'Unknown')}. "
        f"Severity: {inc.get('severity_score', '?')}/10 ({inc.get('severity_label', '?')}). "
        f"Lanes: {inc.get('lanes_affected', '?')}. "
        f"Traffic: {inc.get('traffic_density', '?')}. "
        f"Weather: {inc.get('weather', '?')}."
    )

    reply = chat_query(req.conversation_history, context, req.question)
    return {"reply": reply}


