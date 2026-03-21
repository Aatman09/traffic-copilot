"""
tests/test_routing.py — Tests for routing and ETA calculation logic.
"""
import pytest
from services.routing import estimate_eta

def test_estimate_eta_light_traffic():
    # 40 km/h = 11.11 m/s. 10km = 10000m. 10000 / 11.11 = 900s = 15m
    eta = estimate_eta(10000, "Light")
    assert eta == 15.0

def test_estimate_eta_moderate_traffic():
    # 25 km/h = 6.94 m/s. 10km = 10000m. 10000 / 6.94 = 1440s = 24m
    eta = estimate_eta(10000, "Moderate")
    assert eta == 24.0

def test_estimate_eta_heavy_traffic():
    # 15 km/h = 4.16 m/s. 10km = 10000m. 10000 / 4.16 = 2400s = 40m
    eta = estimate_eta(10000, "Heavy")
    assert eta == 40.0

def test_estimate_eta_gridlock():
    # 8 km/h = 2.22 m/s. 10km = 10000m. 10000 / 2.22 = 4500s = 75m
    eta = estimate_eta(10000, "Gridlock")
    assert eta == 75.0

def test_estimate_eta_zero_distance():
    assert estimate_eta(0, "Moderate") == 0.0

def test_estimate_eta_unknown_density():
    # Should default to Moderate (25 km/h -> 24.0 min for 10km)
    eta = estimate_eta(10000, "UnknownDensity")
    assert eta == 24.0
