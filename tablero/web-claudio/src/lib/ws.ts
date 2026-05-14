// useWebSocket — broker WS suscripción por canal, gating por contexto.

import { useEffect, useRef, useState } from 'react';
import { getToken } from './auth';

interface WsMsg<T = unknown> {
  type: 'snapshot' | 'update' | 'pong' | 'error';
  channel?: string;
  payload?: T;
  code?: string;
  ts?: number;
}

const SOCKETS: Record<string, WebSocket> = {};
const LISTENERS: Record<string, Set<(msg: WsMsg) => void>> = {};

function ensureSocket(): WebSocket | null {
  const token = getToken();
  if (!token) return null;
  const key = 'main';
  if (SOCKETS[key] && SOCKETS[key].readyState <= 1) return SOCKETS[key];
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(
    `${proto}//${location.host}/tablero/api/v2/ws?token=${encodeURIComponent(token)}`
  );
  SOCKETS[key] = ws;
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data) as WsMsg;
      if (msg.channel && LISTENERS[msg.channel]) {
        LISTENERS[msg.channel].forEach((fn) => fn(msg));
      }
    } catch {
      /* ignore */
    }
  };
  ws.onclose = () => {
    delete SOCKETS[key];
  };
  return ws;
}

export function useChannel<T = unknown>(
  channel: string | null
): { data: T | null; connected: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [connected, setConnected] = useState(false);
  const subscribedRef = useRef(false);

  useEffect(() => {
    if (!channel) return;
    const ws = ensureSocket();
    if (!ws) return;

    if (!LISTENERS[channel]) LISTENERS[channel] = new Set();
    const fn = (msg: WsMsg<T>) => {
      if (msg.type === 'snapshot' || msg.type === 'update') {
        setData(msg.payload ?? null);
      } else if (msg.type === 'error') {
        setConnected(false);
      }
    };
    LISTENERS[channel].add(fn);

    const subscribe = () => {
      if (subscribedRef.current) return;
      try {
        ws.send(JSON.stringify({ type: 'subscribe', channel }));
        subscribedRef.current = true;
        setConnected(true);
      } catch {
        /* socket not ready */
      }
    };

    if (ws.readyState === WebSocket.OPEN) {
      subscribe();
    } else {
      ws.addEventListener('open', subscribe, { once: true });
    }

    return () => {
      LISTENERS[channel].delete(fn);
      if (ws.readyState === WebSocket.OPEN && subscribedRef.current) {
        try {
          ws.send(JSON.stringify({ type: 'unsubscribe', channel }));
        } catch {
          /* ignore */
        }
        subscribedRef.current = false;
      }
    };
  }, [channel]);

  return { data, connected };
}
