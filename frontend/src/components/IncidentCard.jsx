/**
 * components/IncidentCard.jsx — Google Maps-style incident card for sidebar.
 */

export default function IncidentCard({ incident, onClick }) {
  const sev = incident.severity_score;
  const label = incident.severity_label || '';
  const street = incident.blocked_street || 'Unknown Road';
  const vehicle = incident.vehicle_type || '';
  const time = (incident.created_at || '').slice(0, 16).replace('T', ' ');

  let sevClass = 'sev-low';
  if (sev >= 8) sevClass = 'sev-critical';
  else if (sev >= 6) sevClass = 'sev-high';
  else if (sev >= 4) sevClass = 'sev-medium';

  return (
    <div className="incident-card" onClick={() => onClick?.(incident)}>
      <div className="incident-card-header">
        <span className="incident-street">🚨 {street}</span>
      </div>
      <div className="incident-meta">
        {vehicle}{vehicle && ' · '}{time}
      </div>
      {sev != null && (
        <span className={`sev-badge ${sevClass}`}>
          {sev}/10 {label}
        </span>
      )}
    </div>
  );
}
