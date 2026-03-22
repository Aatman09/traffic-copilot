"""
services/api_client.py — HTTP client for the FastAPI backend.

The Streamlit admin app calls these instead of importing services directly.
Requires the backend to be running: uvicorn backend.main:app --port 8000
"""

import requests

API_BASE = "http://localhost:8080"


def _url(path: str) -> str:
    return f"{API_BASE}{path}"


def create_incident(data: dict) -> dict:
    """POST /incidents — create a new incident from form data."""
    resp = requests.post(_url("/incidents"), json=data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def analyze_incident(incident_id: int, traffic_density: str = "Moderate") -> dict:
    """POST /incidents/{id}/analyze — run full AI analysis."""
    resp = requests.post(
        _url(f"/incidents/{incident_id}/analyze"),
        json={"incident_id": incident_id, "traffic_density": traffic_density},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_incident(incident_id: int) -> dict | None:
    """GET /incidents/{id}"""
    resp = requests.get(_url(f"/incidents/{incident_id}"), timeout=10)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def list_incidents(status: str | None = None, limit: int = 50) -> list[dict]:
    """GET /incidents — list all or filtered incidents."""
    params = {"limit": limit}
    if status:
        params["status"] = status
    resp = requests.get(_url("/incidents"), params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def resolve_incident(incident_id: int) -> dict:
    """POST /incidents/{id}/resolve"""
    resp = requests.post(_url(f"/incidents/{incident_id}/resolve"), timeout=10)
    resp.raise_for_status()
    return resp.json()


def send_notification(incident_id: int, channel: str,
                      phone_numbers: list[str], message: str | None = None) -> dict:
    """POST /notify — send WhatsApp/SMS alerts."""
    resp = requests.post(_url("/notify"), json={
        "incident_id": incident_id,
        "channel": channel,
        "phone_numbers": phone_numbers,
        "message": message,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()


def preview_route(start_lat: float, start_lng: float,
                  end_lat: float, end_lng: float) -> dict | None:
    """GET /routes/preview — direct route preview (no crash avoidance)."""
    resp = requests.get(_url("/routes/preview"), params={
        "start_lat": start_lat, "start_lng": start_lng,
        "end_lat": end_lat, "end_lng": end_lng,
    }, timeout=15)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def chat(incident_id: int, conversation_history: list, question: str) -> str:
    """POST /chat — multi-turn chat about an incident."""
    resp = requests.post(_url("/chat"), json={
        "incident_id": incident_id,
        "conversation_history": conversation_history,
        "question": question,
    }, timeout=30)
    resp.raise_for_status()
    return resp.json().get("reply", "")
