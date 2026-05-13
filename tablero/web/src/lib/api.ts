import { getToken, clearToken } from './auth';
import type {
  ErrorResponse,
  NoteResponse,
  SearchResponse,
  TimelineFilters,
  TimelineResponse,
  WhoamiResponse,
} from './types';

const API_BASE = (import.meta.env.VITE_API_BASE as string) ?? '';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly detalle?: string,
  ) {
    super(`${status} ${code}${detalle ? ` — ${detalle}` : ''}`);
  }
  get isAuthError() {
    return this.status === 401;
  }
}

export async function fetchJSON<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Accept')) headers.set('Accept', 'application/json');

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const res = await fetch(url, { ...init, headers });

  let body: unknown = null;
  const ctype = res.headers.get('content-type') ?? '';
  if (ctype.includes('application/json')) {
    body = await res.json().catch(() => null);
  } else {
    body = await res.text().catch(() => null);
  }

  if (!res.ok) {
    const err = (body ?? {}) as Partial<ErrorResponse>;
    const apiErr = new ApiError(res.status, err.error ?? 'http_error', err.detalle);
    if (res.status === 401) {
      clearToken();
    }
    throw apiErr;
  }
  return body as T;
}

export function getHealth() {
  return fetchJSON<{ ok: true; service: string; version: string }>('/tablero/api/health');
}

export function getWhoami() {
  return fetchJSON<WhoamiResponse>('/tablero/api/whoami');
}

function buildTimelineQuery(filters: TimelineFilters): string {
  const p = new URLSearchParams();
  if (filters.autor && filters.autor !== 'ambos') p.set('autor', filters.autor);
  if (filters.etiqueta) p.set('etiqueta', filters.etiqueta);
  if (filters.desde) p.set('desde', filters.desde);
  if (filters.hasta) p.set('hasta', filters.hasta);
  const qs = p.toString();
  return qs ? `?${qs}` : '';
}

export function getTimeline(filters: TimelineFilters) {
  return fetchJSON<TimelineResponse>(`/tablero/api/timeline${buildTimelineQuery(filters)}`);
}

export function getBuscar(params: { q: string; autor?: string; etiqueta?: string; desde?: string; hasta?: string; limite?: number }) {
  const p = new URLSearchParams();
  p.set('q', params.q);
  if (params.autor) p.set('autor', params.autor);
  if (params.etiqueta) p.set('etiqueta', params.etiqueta);
  if (params.desde) p.set('desde', params.desde);
  if (params.hasta) p.set('hasta', params.hasta);
  if (params.limite) p.set('limite', String(params.limite));
  return fetchJSON<SearchResponse>(`/tablero/api/buscar?${p}`);
}

export function getNota(path: string) {
  const p = new URLSearchParams({ path });
  return fetchJSON<NoteResponse>(`/tablero/api/nota?${p}`);
}
