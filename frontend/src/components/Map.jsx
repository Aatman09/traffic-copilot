/**
 * components/Map.jsx — Leaflet map with Google Maps aesthetic.
 * Shows: active incident markers, user start/end pins, routes with active selection.
 */

import React, { useEffect } from 'react';
import { MapContainer, LayersControl, TileLayer, Marker, Circle, Polyline, Tooltip, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';

const AHMEDABAD = [23.0225, 72.5714];
const ROUTE_COLORS = ['#1a73e8', '#34a853', '#9334e6', '#e8710a', '#ea4335'];

/* Custom icons */
function pinIcon(color, label) {
  return L.divIcon({
    className: '',
    html: `<div style="position:relative;width:30px;height:42px;">
      <svg width="30" height="42" viewBox="0 0 30 42" fill="none">
        <path d="M15 0C6.72 0 0 6.72 0 15C0 26.25 15 42 15 42C15 42 30 26.25 30 15C30 6.72 23.28 0 15 0Z" fill="${color}"/>
        <circle cx="15" cy="15" r="7" fill="white" fill-opacity="0.9"/>
      </svg>
      <div style="position:absolute;top:7px;left:0;width:30px;text-align:center;font-size:12px;font-weight:700;color:${color};line-height:16px;">${label}</div>
    </div>`,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
  });
}

function crashIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="position:relative;width:24px;height:24px;">
      <div style="position:absolute;width:24px;height:24px;border-radius:50%;background:rgba(234,67,53,.25);animation:crash-pulse 2s ease-out infinite;"></div>
      <div style="position:absolute;top:4px;left:4px;width:16px;height:16px;border-radius:50%;background:#ea4335;border:2px solid #fff;z-index:2;"></div>
    </div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

const START_ICON = pinIcon('#34a853', 'A');
const END_ICON = pinIcon('#1a73e8', 'B');
const CRASH_ICON = crashIcon();

/* Click handler component */
function ClickHandler({ onClick }) {
  useMapEvents({ click: (e) => onClick(e.latlng) });
  return null;
}

/* Fit bounds when routes change */
function FitBounds({ routes, start, end }) {
  const map = useMap();
  useEffect(() => {
    const points = [];
    if (start) points.push(start);
    if (end) points.push(end);
    routes.forEach((r) => r.coords?.forEach((c) => points.push(c)));
    if (points.length >= 2) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [routes, start, end, map]);
  return null;
}

export default function MapView({ incidents, waypoints, routes, activeRoute = 0, onMapClick }) {
  const { start, end } = waypoints;

  return (
    <MapContainer
      center={AHMEDABAD}
      zoom={13}
      className="map-container"
      zoomControl={false}
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Map">
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Satellite">
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="&copy; Esri"
          />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Dark">
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />
        </LayersControl.BaseLayer>
      </LayersControl>

      <ClickHandler onClick={onMapClick} />
      <FitBounds routes={routes} start={start} end={end} />

      {/* Active incident markers with impact zone */}
      {incidents.map((inc) => (
        <React.Fragment key={`inc-${inc.id}`}>
          <Circle
            center={[inc.crash_lat, inc.crash_lng]}
            radius={300}
            pathOptions={{ color: '#ea4335', fillColor: '#ea4335', fillOpacity: 0.08, weight: 1, dashArray: '6 4' }}
          />
          <Marker
            position={[inc.crash_lat, inc.crash_lng]}
            icon={CRASH_ICON}
          >
            <Tooltip direction="top" offset={[0, -12]}>
              {inc.blocked_street || 'Crash'} — {inc.severity_score || '?'}/10
            </Tooltip>
          </Marker>
        </React.Fragment>
      ))}

      {/* User pins */}
      {start && <Marker position={start} icon={START_ICON} />}
      {end && <Marker position={end} icon={END_ICON} />}

      {/* Routes — inactive first (behind), active on top */}
      {routes.map((r, i) => {
        if (i === activeRoute) return null; // render active last
        const color = ROUTE_COLORS[i % ROUTE_COLORS.length];
        if (!r.coords || r.coords.length === 0) return null;
        return (
          <React.Fragment key={`route-${i}`}>
            <Polyline
              positions={r.coords}
              pathOptions={{ color: '#202124', weight: 5, opacity: 0.15 }}
            />
            <Polyline
              positions={r.coords}
              pathOptions={{ color, weight: 3, opacity: 0.4 }}
            >
              <Tooltip sticky>Route {r.rank} — {r.eta_minutes ?? '?'} min, {(r.distance_m / 1000).toFixed(1)} km</Tooltip>
            </Polyline>
          </React.Fragment>
        );
      })}

      {/* Active route — rendered last so it's on top */}
      {routes[activeRoute] && routes[activeRoute].coords?.length > 0 && (() => {
        const r = routes[activeRoute];
        const color = ROUTE_COLORS[activeRoute % ROUTE_COLORS.length];
        return (
          <React.Fragment key="route-active">
            <Polyline
              positions={r.coords}
              pathOptions={{ color: '#202124', weight: 8, opacity: 0.35 }}
            />
            <Polyline
              positions={r.coords}
              pathOptions={{ color, weight: 5, opacity: 0.95 }}
            >
              <Tooltip sticky>Route {r.rank} — {r.eta_minutes ?? '?'} min, {(r.distance_m / 1000).toFixed(1)} km</Tooltip>
            </Polyline>
          </React.Fragment>
        );
      })()}
    </MapContainer>
  );
}
