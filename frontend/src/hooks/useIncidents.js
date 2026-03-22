/**
 * hooks/useIncidents.js — WebSocket + polling hook for live incident feed.
 * WebSocket for instant updates, polling every 5s as fallback.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchActiveIncidents } from '../services/api';

const POLL_INTERVAL = 5000; // 5 seconds

export default function useIncidents() {
  const [incidents, setIncidents] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const pollTimer = useRef(null);

  /* Poll active incidents from REST API */
  const poll = useCallback(async () => {
    try {
      const data = await fetchActiveIncidents();
      setIncidents(data);
    } catch {
      // Backend might be down — ignore
    }
  }, []);

  const connect = useCallback(() => {
    // Use Vite proxy for WebSocket in dev, direct for production
    const loc = window.location;
    const wsUrl = `${loc.protocol === 'https:' ? 'wss' : 'ws'}://${loc.host}/ws/incidents`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (reconnectTimer.current) {
          clearTimeout(reconnectTimer.current);
          reconnectTimer.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === 'initial') {
            setIncidents(msg.incidents || []);
          } else if (msg.type === 'new_incident') {
            setIncidents((prev) => [msg.incident, ...prev]);
          } else if (msg.type === 'incident_updated') {
            setIncidents((prev) =>
              prev.map((inc) => (inc.id === msg.incident.id ? msg.incident : inc))
            );
          } else if (msg.type === 'incident_resolved') {
            setIncidents((prev) =>
              prev.filter((inc) => inc.id !== msg.incident_id)
            );
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    } catch {
      // WebSocket connection failed — rely on polling
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 5000);
    }
  }, []);

  useEffect(() => {
    // Connect WebSocket
    connect();

    // Start polling as fallback (catches DB-level changes from admin app)
    poll();
    pollTimer.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, [connect, poll]);

  return { incidents, connected };
}
