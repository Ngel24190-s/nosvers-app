import { getToken } from '../../../lib/auth';

const API_BASE = ((import.meta.env.VITE_API_BASE as string) ?? '').replace(/\/+$/, '');
const API_ROOT = `${API_BASE}/tablero/api/v2/automatizaciones`;

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken() ?? '';
  const headers = new Headers(init?.headers);
  headers.set('Authorization', `Bearer ${token}`);
  if (init?.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const r = await fetch(`${API_ROOT}${path}`, { ...init, headers });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status}: ${text}`);
  }
  return r.json() as Promise<T>;
}

export interface AutomationSummary {
  id: string;
  nombre: string;
  autor: 'angel' | 'africa' | 'claude';
  activo: boolean;
  trigger_tipo: string;
  modificado: string;
  last_run: { ts: string; status: string; duration_ms: number } | null;
}

export interface Automation {
  id: string;
  nombre: string;
  autor: 'angel' | 'africa' | 'claude';
  creado: string;
  modificado: string;
  activo: boolean;
  trigger: { tipo: string; [k: string]: unknown };
  acciones: Array<{ tipo: string; [k: string]: unknown }>;
  metadatos?: Record<string, unknown>;
}

export interface AutomationCreate {
  nombre: string;
  activo: boolean;
  trigger: { tipo: string; [k: string]: unknown };
  acciones: Array<{ tipo: string; [k: string]: unknown }>;
  metadatos?: Record<string, unknown>;
}

export interface CatalogEntry {
  schema: Record<string, unknown>;
  available: boolean;
  label: string;
  icon: string;
  reason?: string;
}

export interface Catalog {
  triggers: Record<string, CatalogEntry>;
  actions: Record<string, CatalogEntry>;
}

export interface ExecutionLog {
  execution_id: string;
  automation_id: string;
  automation_nombre: string;
  trigger: { tipo: string; payload: unknown };
  autor_trigger: string;
  autor_automation: string;
  started_at: string;
  ended_at: string;
  duration_ms: number;
  status: 'ok' | 'partial' | 'error' | 'interrupted';
  dry_run?: boolean;
  steps: Array<{
    n: number;
    action_tipo: string;
    ok: boolean;
    duration_ms: number;
    output?: unknown;
    would_do?: unknown;
    error?: string;
  }>;
}

export const apiAutomations = {
  list: () => req<{ items: AutomationSummary[]; corruptos: string[] }>(''),
  get: (id: string) => req<Automation>(`/${id}`),
  create: (body: AutomationCreate) => req<{ ok: true; id: string }>('', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: AutomationCreate) => req<{ ok: true }>(`/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  remove: (id: string) => req<{ ok: true; archived_path: string }>(`/${id}`, { method: 'DELETE' }),
  run: (id: string, trigger_payload?: unknown) =>
    req<ExecutionLog>(`/${id}/run`, { method: 'POST', body: JSON.stringify({ trigger_payload: trigger_payload ?? {} }) }),
  test: (id: string, trigger_payload?: unknown) =>
    req<ExecutionLog>(`/${id}/test`, { method: 'POST', body: JSON.stringify({ trigger_payload: trigger_payload ?? {} }) }),
  logs: (id: string, date?: string) =>
    req<{ date: string; items: ExecutionLog[] }>(`/${id}/logs${date ? `?date=${date}` : ''}`),
  catalogo: () => req<Catalog>('/catalogo'),
  reload: () => req<{ ok: true; loaded: number; errors: string[] }>('/reload', { method: 'POST' }),
};
