/**
 * hooks/useIncidents.js — WebSocket + polling hook for live incident feed.
 * WebSocket for instant updates, polling every 10s as fallback for
 * changes made directly to the DB (e.g. admin app resolving incidents).
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchActiveIncidents } from '../services/api';

const POLL_INTERVAL = 10000; // 10 seconds

export default function useIncidents() {
  const [incidents, setIncidents] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const pollTimer = useRef(null);

  /* Poll active incidents from REST API as fallback */
  const poll = useCallback(async () => {
    try {
      const data = await fetchActiveIncidents();
      setIncidents(data);
    } catch {
      // Backend might be down — ignore
    }
  }, []);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.hostname}:8080/ws/incidents`;

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
  }, []);

  useEffect(() => {
    // Connect WebSocket
    connect();

    // Start polling as fallback
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
