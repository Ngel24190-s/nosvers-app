import { useEffect, useRef, useState, useCallback } from 'react';

export type CockpitChannel =
  | 'health'
  | 'claude'
  | 'activity'
  | 'agentes'
  | 'revenue'
  | 'aegis'
  | 'wake'
  | 'automation'
  // 006-claudio-voz-cockpit: familia/admin
  | 'recordatorios'
  | 'gastos'
  | 'compras'
  | 'medicacion'
  | 'coche'
  | 'menu_dia'
  | 'bris';

export type WsStatus = 'connecting' | 'connected' | 'reconnecting' | 'failed';

interface SnapshotMsg {
  type: 'snapshot' | 'update';
  channel: CockpitChannel;
  payload: unknown;
  ts: number;
}

interface PongMsg {
  type: 'pong';
  ts: number;
}

interface ErrorMsg {
  type: 'error';
  code: string;
  channel?: string;
}

type ServerMsg = SnapshotMsg | PongMsg | ErrorMsg;

type Listener = (payload: unknown, meta: { channel: CockpitChannel; ts: number; firstSnapshot: boolean }) => void;

const BACKOFF_MS = [1000, 2000, 4000, 8000, 16000, 30000];

export interface UseWebSocketOptions {
  token: string;
  url: string;
}

export interface UseWebSocketReturn {
  status: WsStatus;
  subscribe: (channel: CockpitChannel, listener: Listener) => () => void;
  send: (msg: object) => void;
}

/**
 * useWebSocket — single WS multiplexed por canales + reconexión exponencial.
 * No re-renderiza el componente que lo invoca cuando llega un mensaje:
 * los listeners reciben los payloads directamente. El consumer aplica su propio state.
 */
export function useWebSocket({ token, url }: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const subscribedRef = useRef<Set<CockpitChannel>>(new Set());
  const listenersRef = useRef<Map<CockpitChannel, Set<Listener>>>(new Map());
  const closedByUserRef = useRef(false);
  const [status, setStatus] = useState<WsStatus>('connecting');

  const send = useCallback((msg: object) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  const connect = useCallback(() => {
    if (!token) return;
    closedByUserRef.current = false;
    const fullUrl = `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(fullUrl);
    } catch {
      setStatus('failed');
      return;
    }
    wsRef.current = ws;
    setStatus(attemptRef.current === 0 ? 'connecting' : 'reconnecting');

    ws.onopen = () => {
      attemptRef.current = 0;
      setStatus('connected');
      // re-subscribe a todos los canales pedidos
      subscribedRef.current.forEach((ch) => {
        ws.send(JSON.stringify({ type: 'subscribe', channel: ch }));
      });
    };

    ws.onmessage = (ev) => {
      let msg: ServerMsg;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      if (msg.type === 'snapshot' || msg.type === 'update') {
        const listeners = listenersRef.current.get(msg.channel);
        if (listeners) {
          listeners.forEach((l) =>
            l(msg.payload, {
              channel: msg.channel,
              ts: msg.ts,
              firstSnapshot: msg.type === 'snapshot',
            }),
          );
        }
      }
    };

    ws.onclose = (ev) => {
      wsRef.current = null;
      if (closedByUserRef.current) return;
      // backoff exponencial
      const delay = BACKOFF_MS[Math.min(attemptRef.current, BACKOFF_MS.length - 1)];
      attemptRef.current += 1;
      setStatus(attemptRef.current >= BACKOFF_MS.length * 2 ? 'failed' : 'reconnecting');
      // si el close fue 4401 (auth), no reintenta
      if (ev.code === 4401) {
        setStatus('failed');
        return;
      }
      setTimeout(connect, delay);
    };

    ws.onerror = () => {
      // dejamos que onclose maneje el reintento
    };
  }, [token, url]);

  useEffect(() => {
    connect();
    return () => {
      closedByUserRef.current = true;
      wsRef.current?.close(1000, 'cleanup');
    };
  }, [connect]);

  const subscribe = useCallback(
    (channel: CockpitChannel, listener: Listener) => {
      let listeners = listenersRef.current.get(channel);
      if (!listeners) {
        listeners = new Set();
        listenersRef.current.set(channel, listeners);
      }
      listeners.add(listener);
      // si todavía no hemos pedido subscribe, hacerlo
      if (!subscribedRef.current.has(channel)) {
        subscribedRef.current.add(channel);
        send({ type: 'subscribe', channel });
      }
      // unsubscribe local
      return () => {
        const ls = listenersRef.current.get(channel);
        if (!ls) return;
        ls.delete(listener);
        if (ls.size === 0) {
          listenersRef.current.delete(channel);
          subscribedRef.current.delete(channel);
          send({ type: 'unsubscribe', channel });
        }
      };
    },
    [send],
  );

  return { status, subscribe, send };
}
