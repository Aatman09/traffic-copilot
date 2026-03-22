/**
 * components/RouteCard.jsx — Google Maps-style route result card.
 */

const COLORS = ['#1a73e8', '#34a853', '#9334e6', '#e8710a', '#ea4335'];

export default function RouteCard({ route, index }) {
  const color = COLORS[index % COLORS.length];
  const best = index === 0;

  return (
    <div className="route-card" style={{ borderLeftColor: color }}>
      {best && <span className="route-best-badge">Best route</span>}
      <div className="route-eta">{route.eta_minutes ?? '?'} min</div>
      <div className="route-dist">{route.distance_m} m</div>
      <div className="route-streets">{route.street_summary || 'Local Roads'}</div>
    </div>
  );
}
