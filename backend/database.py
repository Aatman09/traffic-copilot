"""
backend/database.py — SQLite database for incidents, shared by admin + user apps.
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "incidents.db")


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crash_lat REAL NOT NULL,
            crash_lng REAL NOT NULL,
            start_lat REAL,
            start_lng REAL,
            end_lat REAL,
            end_lng REAL,
            blocked_street TEXT,
            vehicle_type TEXT,
            lanes_affected TEXT,
            traffic_density TEXT,
            weather TEXT,
            notes TEXT,
            severity_score REAL,
            severity_label TEXT,
            status TEXT DEFAULT 'active',
            analysis JSON,
            routes JSON,
            dispatch JSON,
            congestion JSON,
            photo_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_incident(data: dict) -> int:
    """Insert a new incident and return its ID."""
    conn = _get_conn()
    cur = conn.execute("""
        INSERT INTO incidents (
            crash_lat, crash_lng, start_lat, start_lng, end_lat, end_lng,
            blocked_street, vehicle_type, lanes_affected, traffic_density,
            weather, notes, severity_score, severity_label, status,
            analysis, routes, dispatch, congestion, photo_url, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("crash_lat"), data.get("crash_lng"),
        data.get("start_lat"), data.get("start_lng"),
        data.get("end_lat"), data.get("end_lng"),
        data.get("blocked_street"),
        data.get("vehicle_type"), data.get("lanes_affected"),
        data.get("traffic_density"), data.get("weather"),
        data.get("notes"),
        data.get("severity_score"), data.get("severity_label"),
        data.get("status", "active"),
        json.dumps(data.get("analysis")) if data.get("analysis") else None,
        json.dumps(data.get("routes")) if data.get("routes") else None,
        json.dumps(data.get("dispatch")) if data.get("dispatch") else None,
        json.dumps(data.get("congestion")) if data.get("congestion") else None,
        data.get("photo_url"),
        datetime.now().isoformat(),
    ))
    conn.commit()
    incident_id = cur.lastrowid
    conn.close()
    return incident_id


def get_incident(incident_id: int) -> dict | None:
    """Fetch a single incident by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def get_active_incidents() -> list[dict]:
    """Fetch all active incidents (for the user app live map)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE status = 'active' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_incidents(limit: int = 50) -> list[dict]:
    """Fetch all incidents (admin history)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_incident(incident_id: int, data: dict):
    """Update an incident with analysis results."""
    fields = []
    values = []
    for key in ["severity_score", "severity_label", "status", "blocked_street",
                 "start_lat", "start_lng", "end_lat", "end_lng"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(data[key])
    for key in ["analysis", "routes", "dispatch", "congestion"]:
        if key in data:
            fields.append(f"{key} = ?")
            values.append(json.dumps(data[key]))
    if not fields:
        return
    values.append(incident_id)
    conn = _get_conn()
    conn.execute(f"UPDATE incidents SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def resolve_incident(incident_id: int):
    """Mark an incident as resolved."""
    conn = _get_conn()
    conn.execute("UPDATE incidents SET status = 'resolved' WHERE id = ?", (incident_id,))
    conn.commit()
    conn.close()


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a dict, parsing JSON fields."""
    d = dict(row)
    for key in ["analysis", "routes", "dispatch", "congestion"]:
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
