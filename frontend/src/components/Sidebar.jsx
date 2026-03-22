/**
 * components/Sidebar.jsx — Google Maps directions panel (floating).
 * Uses SVG icons instead of emojis for crisp, consistent rendering.
 */

import { useState, useRef, useEffect } from 'react';
import { geocode } from '../services/api';
import {
  CarIcon, CloseIcon, SwapIcon, SearchIcon, ClearIcon,
  PinIcon, WarningIcon, ChevronIcon,
} from './Icons';

const ROUTE_COLORS = ['#1a73e8', '#34a853', '#9334e6', '#e8710a', '#ea4335'];

/* ── Search input with autocomplete dropdown ──── */
function SearchInput({ placeholder, value, onSelect, onClear }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const timerRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleInput = (e) => {
    const q = e.target.value;
    setQuery(q);
    if (timerRef.current) clearTimeout(timerRef.current);
    if (q.length < 2) { setResults([]); setOpen(false); return; }
    timerRef.current = setTimeout(async () => {
      try {
        const res = await geocode(q);
        setResults(res);
        setOpen(res.length > 0);
      } catch { setResults([]); }
    }, 400);
  };

  const handleSelect = (item) => {
    setQuery(item.short);
    setOpen(false);
    setResults([]);
    onSelect(item);
  };

  const handleClear = () => {
    setQuery('');
    setResults([]);
    setOpen(false);
    onClear?.();
  };

  useEffect(() => {
    if (value && !query) setQuery(`${value[0].toFixed(5)}, ${value[1].toFixed(5)}`);
    if (!value) setQuery('');
  }, [value]);

  return (
    <div className="search-field" ref={boxRef}>
      <input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={handleInput}
        onFocus={() => results.length > 0 && setOpen(true)}
      />
      {query ? (
        <button className="field-icon" onClick={handleClear} aria-label="Clear">
          <ClearIcon />
        </button>
      ) : (
        <button className="field-icon" aria-label="Search">
          <SearchIcon />
        </button>
      )}
      {open && (
        <ul className="search-dropdown">
          {results.map((r, i) => (
            <li key={i} className="search-result" onClick={() => handleSelect(r)}>
              <span className="search-result-icon" style={{ color: '#ea4335' }}>
                <PinIcon />
              </span>
              <div>
                <div className="search-result-name">{r.short}</div>
                <div className="search-result-addr">{r.name}</div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ── Route card ────────────────────────────────── */
function RouteCard({ route, index, isActive, onClick }) {
  const via = route.street_summary || 'Local Roads';
  const km = (route.distance_m / 1000).toFixed(1);
  const color = ROUTE_COLORS[index % ROUTE_COLORS.length];

  return (
    <div
      className={`route-card ${isActive ? 'route-active' : ''}`}
      onClick={onClick}
      style={{ borderLeft: `4px solid ${color}` }}
    >
      <div className="route-card-icon" style={{ color: isActive ? color : '#5f6368' }}>
        <CarIcon />
      </div>
      <div className="route-card-main">
        <div className="route-via">via {via}</div>
        <div className="route-desc">
          {index === 0 ? 'Fastest route avoiding crashes' : 'Alternative route avoiding crashes'}
        </div>
      </div>
      <div className="route-card-right">
        <div className="route-time" style={isActive ? { color } : {}}>{route.eta_minutes ?? '?'} min</div>
        <div className="route-distance">{km} km</div>
      </div>
    </div>
  );
}

/* ── Incident card ─────────────────────────────── */
function IncidentCard({ incident }) {
  const sev = incident.severity_score;
  const label = incident.severity_label || '';
  const street = incident.blocked_street || 'Unknown Road';
  const vehicle = incident.vehicle_type || '';
  const time = (incident.created_at || '').slice(11, 16);

  let sevClass = 'sev-low';
  if (sev >= 8) sevClass = 'sev-critical';
  else if (sev >= 6) sevClass = 'sev-high';
  else if (sev >= 4) sevClass = 'sev-medium';

  return (
    <div className="incident-card">
      <div className="incident-card-icon" style={{ color: '#ea4335' }}>
        <WarningIcon />
      </div>
      <div className="incident-card-body">
        <div className="incident-street">{street}</div>
        <div className="incident-meta">{vehicle}{vehicle && ' · '}{time}</div>
        {sev != null && <span className={`sev-badge ${sevClass}`}>{sev}/10 {label}</span>}
      </div>
    </div>
  );
}

/* ── Main Panel ────────────────────────────────── */
export default function Sidebar({
  incidents,
  nearbyIncidents = [],
  connected,
  waypoints,
  routes,
  activeRoute = 0,
  loading,
  crashesAvoided,
  onStartSelect,
  onEndSelect,
  onStartClear,
  onEndClear,
  onSwap,
  onFindRoutes,
  onReset,
  onRouteSelect,
}) {
  const [incidentsOpen, setIncidentsOpen] = useState(false);
  const { start, end } = waypoints;
  const bothSet = start != null && end != null;
  const displayIncidents = routes.length > 0 ? nearbyIncidents : incidents;

  return (
    <div className="directions-panel">
      {/* Directions card */}
      <div className="directions-card">
        {/* Header */}
        <div className="transport-modes">
          <PinIcon size="20" />
          <span className="panel-title">Safe Commute</span>
          <button className="transport-close" onClick={onReset} aria-label="Reset">
            <CloseIcon />
          </button>
        </div>

        {/* Search inputs */}
        <div className="search-area">
          <div className="dots-column">
            <div className="dot-start" />
            <div className="dot-connector" />
            <div className="dot-end" />
          </div>
          <div className="inputs-column">
            <SearchInput
              placeholder="Choose starting point, or click on the map"
              value={start}
              onSelect={(item) => onStartSelect([item.lat, item.lng])}
              onClear={onStartClear}
            />
            <SearchInput
              placeholder="Choose destination, or click on the map"
              value={end}
              onSelect={(item) => onEndSelect([item.lat, item.lng])}
              onClear={onEndClear}
            />
          </div>
          <div className="swap-column">
            <button className="swap-btn" onClick={onSwap} title="Swap start and end" aria-label="Swap">
              <SwapIcon />
            </button>
          </div>
        </div>

        {/* Find routes button */}
        <div className="actions-bar">
          <button
            className="btn-directions"
            disabled={!bothSet || loading}
            onClick={onFindRoutes}
          >
            {loading ? (
              <><span className="spinner" /> Computing...</>
            ) : (
              <>
                <SearchIcon />
                Find Safe Routes
              </>
            )}
          </button>
        </div>
      </div>

      {/* Route results */}
      {routes.length > 0 && (
        <div className="routes-panel">
          <div className="routes-header">
            <span className="routes-header-title">
              {routes.length} route{routes.length !== 1 ? 's' : ''} found
            </span>
            {crashesAvoided > 0 && (
              <span className="crashes-badge">
                <WarningIcon /> {crashesAvoided} crash{crashesAvoided !== 1 ? 'es' : ''} avoided
              </span>
            )}
          </div>
          {routes.map((r, i) => (
            <RouteCard
              key={i}
              route={r}
              index={i}
              isActive={i === activeRoute}
              onClick={() => onRouteSelect(i)}
            />
          ))}
        </div>
      )}

      {/* Active incidents */}
      {displayIncidents.length > 0 && (
        <div className="incidents-panel">
          <div
            className="incidents-header"
            onClick={() => setIncidentsOpen(!incidentsOpen)}
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <WarningIcon size="16" />
              {routes.length > 0
                ? `${displayIncidents.length} incident${displayIncidents.length !== 1 ? 's' : ''} on your route`
                : 'Active incidents'
              }
              <span className={`live-dot ${connected ? 'live' : 'offline'}`} style={{ position: 'relative', top: 0, left: 0 }} />
            </div>
            <ChevronIcon up={incidentsOpen} />
          </div>
          {incidentsOpen && (
            <div className="incidents-list" style={{ padding: '0 16px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {displayIncidents.map((inc) => (
                <IncidentCard key={inc.id} incident={inc} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
