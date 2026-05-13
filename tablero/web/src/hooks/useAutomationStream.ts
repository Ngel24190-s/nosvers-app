import { useEffect, useState } from 'react';
import type { UseWebSocketReturn } from './useWebSocket';

export interface AutomationEvent {
  event: 'started' | 'step' | 'finished' | 'toast';
  execution_id?: string;
  automation_id?: string;
  automation_nombre?: string;
  status?: 'ok' | 'partial' | 'error' | 'interrupted';
  duration_ms?: number;
  n?: number;
  action_tipo?: string;
  ok?: boolean;
  level?: 'ok' | 'warn' | 'error';
  text?: string;
  ts?: number;
  trigger?: { tipo: string; payload: unknown };
}

export interface RecentExecution {
  execution_id: string;
  automation_id: string;
  automation_nombre: string;
  ts: string;
  status: 'ok' | 'partial' | 'error' | 'interrupted';
  duration_ms: number;
  in_progress?: boolean;
}

export function useAutomationStream(ws: UseWebSocketReturn) {
  const [recent, setRecent] = useState<RecentExecution[]>([]);
  const [hasSnapshot, setHasSnapshot] = useState(false);

  useEffect(() => {
    return ws.subscribe('automation', (payload, meta) => {
      const p = payload as { recent?: RecentExecution[]; event?: string } | AutomationEvent;
      if (meta.firstSnapshot && typeof p === 'object' && p !== null && 'recent' in p && Array.isArray(p.recent)) {
        setRecent(p.recent.slice(-10));
        setHasSnapshot(true);
        return;
      }
      if (typeof p === 'object' && p !== null && 'event' in p) {
        const evt = p as AutomationEvent;
        if (evt.event === 'started') {
          setRecent((prev) => {
            const next: RecentExecution = {
              execution_id: evt.execution_id || `${Date.now()}`,
              automation_id: evt.automation_id || '',
              automation_nombre: evt.automation_nombre || evt.automation_id || '',
              ts: new Date(meta.ts * 1000).toISOString(),
              status: 'interrupted',
              duration_ms: 0,
              in_progress: true,
            };
            return [...prev, next].slice(-10);
          });
        } else if (evt.event === 'finished') {
          setRecent((prev) =>
            prev
              .map((r) =>
                r.execution_id === evt.execution_id
                  ? {
                      ...r,
                      status: evt.status || 'ok',
                      duration_ms: evt.duration_ms || 0,
                      in_progress: false,
                    }
                  : r,
              )
              .slice(-10),
          );
        }
      }
    });
  }, [ws]);

  return { recent, hasSnapshot };
}
