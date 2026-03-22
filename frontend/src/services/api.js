/**
 * services/api.js — REST client for the FastAPI backend.
 * All calls go through the Vite proxy (/api → localhost:8080).
 */

const BASE = '/api';

export async function fetchActiveIncidents() {
  const res = await fetch(`${BASE}/incidents?status=active`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchAllIncidents(limit = 50) {
  const res = await fetch(`${BASE}/incidents?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchIncident(id) {
  const res = await fetch(`${BASE}/incidents/${id}`);
  if (!res.ok) throw new Error('Incident not found');
  return res.json();
}

export async function createIncident(data) {
  const res = await fetch(`${BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create incident');
  return res.json();
}

export async function analyzeIncident(incidentId, trafficDensity = 'Moderate') {
  const res = await fetch(`${BASE}/incidents/${incidentId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ incident_id: incidentId, traffic_density: trafficDensity }),
  });
  if (!res.ok) throw new Error('Analysis failed');
  return res.json();
}

export async function previewRoute(startLat, startLng, endLat, endLng) {
  const params = new URLSearchParams({
    start_lat: startLat, start_lng: startLng,
    end_lat: endLat, end_lng: endLng,
  });
  const res = await fetch(`${BASE}/routes/preview?${params}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error('Preview failed');
  return res.json();
}

export async function findSafeRoutes(startLat, startLng, endLat, endLng, trafficDensity = 'Moderate') {
  const res = await fetch(`${BASE}/routes/safe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      start_lat: startLat, start_lng: startLng,
      end_lat: endLat, end_lng: endLng,
      traffic_density: trafficDensity,
    }),
  });
  if (!res.ok) throw new Error('Safe route failed');
  return res.json();
}

/**
 * Geocode a text query using Nominatim (free, OpenStreetMap).
 * Biased to Ahmedabad for better results.
 */
export async function geocode(query) {
  const params = new URLSearchParams({
    q: `${query}, Ahmedabad, Gujarat, India`,
    format: 'json',
    limit: '5',
    addressdetails: '1',
    viewbox: '72.45,22.90,72.70,23.15',
    bounded: '1',
  });
  const res = await fetch(`https://nominatim.openstreetmap.org/search?${params}`, {
    headers: { 'User-Agent': 'TrafficCoPilot/1.0' },
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.map((item) => ({
    lat: parseFloat(item.lat),
    lng: parseFloat(item.lon),
    name: item.display_name,
    short: item.name || item.display_name.split(',')[0],
  }));
}

