"""
tests/test_models.py — Tests for Incident, Route, and IncidentLog
"""
import pytest
import os
import json
from models.incident import Incident, Route, IncidentLog

# Use a temporary file for tests
TEST_LOG_FILE = "tests/_test_incident_log.json"

@pytest.fixture
def temp_log():
    log = IncidentLog(filepath=TEST_LOG_FILE)
    log.clear()
    yield log
    if os.path.exists(TEST_LOG_FILE):
        os.remove(TEST_LOG_FILE)


def test_incident_creation():
    inc = Incident(
        start_lat=23.0, start_lng=72.5,
        end_lat=23.1, end_lng=72.6,
        crash_lat=23.05, crash_lng=72.55,
        blocked_street="SG Highway",
        severity_score=8
    )
    assert inc.blocked_street == "SG Highway"
    assert inc.severity_score == 8
    assert inc.vehicle_type == "Car"  # default

    d = inc.to_dict()
    assert d["crash_lat"] == 23.05
    assert d["severity_score"] == 8

    # From dict
    inc2 = Incident.from_dict(d)
    assert inc2.blocked_street == "SG Highway"


def test_route_creation():
    r = Route(
        coords=[(23.0, 72.5), (23.1, 72.6)],
        nodes=[1, 2],
        distance_m=1500,
        street_summary="Main St",
        rank=1,
        eta_minutes=4.5
    )
    assert r.distance_m == 1500
    assert r.eta_minutes == 4.5


def test_incident_log(temp_log):
    assert temp_log.count() == 0

    inc = Incident(
        start_lat=23.0, start_lng=72.5,
        end_lat=23.1, end_lng=72.6,
        crash_lat=23.05, crash_lng=72.55
    )
    temp_log.save(inc, analysis={"incident_summary": "Test Crash"}, routes=[{"rank": 1}])

    assert temp_log.count() == 1
    records = temp_log.load()
    assert len(records) == 1
    assert records[0]["route_count"] == 1
    assert records[0]["analysis_summary"] == "Test Crash"
    assert records[0]["incident"]["crash_lat"] == 23.05

    temp_log.clear()
    assert temp_log.count() == 0
