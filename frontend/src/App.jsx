/**
 * App.jsx — Main layout: full-bleed map + floating Google Maps-style directions panel.
 */

import { useState, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import MapView from './components/Map';
import useIncidents from './hooks/useIncidents';
import { findSafeRoutes } from './services/api';
import './App.css';

export default function App() {
  const { incidents, connected } = useIncidents();

  const [clickMode, setClickMode] = useState('start'); // start → end → done
  const [start, setStart] = useState(null);
  const [end, setEnd] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [activeRoute, setActiveRoute] = useState(0);
  const [loading, setLoading] = useState(false);

  /* Map click — fallback to clicking points on map */
  const handleMapClick = useCallback((latlng) => {
    const pos = [latlng.lat, latlng.lng];
    if (clickMode === 'start') {
      setStart(pos);
      setEnd(null);
      setRoutes([]);
      setActiveRoute(0);
      setClickMode('end');
    } else if (clickMode === 'end') {
      setEnd(pos);
      setClickMode('done');
    }
  }, [clickMode]);

  /* Search-based selection */
  const handleStartSelect = useCallback((pos) => {
    setStart(pos);
    setRoutes([]);
    setActiveRoute(0);
    if (!end) setClickMode('end');
    else setClickMode('done');
  }, [end]);

  const handleEndSelect = useCallback((pos) => {
    setEnd(pos);
    setRoutes([]);
    setActiveRoute(0);
    setClickMode('done');
  }, []);

  const handleStartClear = useCallback(() => {
    setStart(null);
    setRoutes([]);
    setActiveRoute(0);
    setClickMode('start');
  }, []);

  const handleEndClear = useCallback(() => {
    setEnd(null);
    setRoutes([]);
    setActiveRoute(0);
    setClickMode('end');
  }, []);

  /* Swap start ↔ end */
  const handleSwap = useCallback(() => {
    setStart(end);
    setEnd(start);
    setRoutes([]);
    setActiveRoute(0);
  }, [start, end]);

  /* Find safe routes — uses /routes/safe which avoids ALL active crashes */
  const handleFindRoutes = useCallback(async () => {
    if (!start || !end) return;
    setLoading(true);
    setActiveRoute(0);
    try {
      const result = await findSafeRoutes(start[0], start[1], end[0], end[1]);
      if (result.routes) {
        setRoutes(result.routes);
      } else if (result.coords) {
        setRoutes([{ ...result, rank: 1, street_summary: 'Direct Route' }]);
      }
    } catch (err) {
      console.error('Route error:', err);
      alert('Failed to compute routes. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, [start, end]);

  /* Reset everything */
  const handleReset = useCallback(() => {
    setStart(null);
    setEnd(null);
    setRoutes([]);
    setActiveRoute(0);
    setClickMode('start');
  }, []);

  /* Filter incidents to only those near the route path (within ~2km) */
  const nearbyIncidents = routes.length > 0
    ? incidents.filter((inc) => {
        return routes.some((route) =>
          route.coords?.some((coord) => {
            const dLat = inc.crash_lat - coord[0];
            const dLng = inc.crash_lng - coord[1];
            return Math.sqrt(dLat * dLat + dLng * dLng) < 0.02; // ~2km
          })
        );
      })
    : incidents;

  return (
    <div className="app-layout">
      <Sidebar
        incidents={incidents}
        nearbyIncidents={nearbyIncidents}
        connected={connected}
        waypoints={{ start, end }}
        routes={routes}
        activeRoute={activeRoute}
        loading={loading}
        crashesAvoided={routes.length > 0 ? nearbyIncidents.length : 0}
        onStartSelect={handleStartSelect}
        onEndSelect={handleEndSelect}
        onStartClear={handleStartClear}
        onEndClear={handleEndClear}
        onSwap={handleSwap}
        onFindRoutes={handleFindRoutes}
        onReset={handleReset}
        onRouteSelect={setActiveRoute}
      />
      <main className="map-area">
        <MapView
          incidents={nearbyIncidents}
          waypoints={{ start, end }}
          routes={routes}
          activeRoute={activeRoute}
          onMapClick={handleMapClick}
        />
      </main>
    </div>
  );
}
