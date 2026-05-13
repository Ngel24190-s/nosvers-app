import { getToken, clearToken } from './auth';
import type {
  CapturarRequest,
  CapturarResponse,
  EditarRequest,
  EditarResponse,
  ErrorResponse,
  NoteResponse,
  SearchResponse,
  StaleModifiedAtError,
  TimelineFilters,
  TimelineResponse,
  WhoamiResponse,
} from './types';

export class ConcurrencyError extends Error {
  constructor(public readonly currentModifiedAt: string) {
    super(`stale_modified_at; current=${currentModifiedAt}`);
  }
}

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

// ─── Fase B+C v2 endpoints ────────────────────────────────────────────────────

export function capturarNota(body: CapturarRequest) {
  return fetchJSON<CapturarResponse>('/tablero/api/v2/capturar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

// Fase B+C P2 fetchers

export function archivarNota(path: string, ifMatch: string, archive_reason?: string) {
  return fetchJSON<{ ok: true; new_path: string; archived_at: string }>(
    '/tablero/api/v2/nota/archivar',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'If-Match': ifMatch },
      body: JSON.stringify({ path, archive_reason }),
    },
  );
}

export function restaurarNota(path: string) {
  return fetchJSON<{ ok: true; new_path: string; fecha: string; ts: string }>(
    '/tablero/api/v2/nota/restaurar',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    },
  );
}

export function listProyectos() {
  return fetchJSON<{ ok: true; proyectos: import('./types').Proyecto[] }>(
    '/tablero/api/v2/proyectos',
  );
}

export function patchProyecto(slug: string, ifMatch: string, fields: Partial<import('./types').Proyecto>) {
  return fetchJSON<import('./types').Proyecto & { ok: true }>(
    '/tablero/api/v2/proyectos',
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'If-Match': ifMatch },
      body: JSON.stringify({ slug, ...fields }),
    },
  );
}

export function getWikiIndex(target?: string) {
  const qs = target ? `?target=${encodeURIComponent(target)}` : '';
  return fetchJSON<{
    ok: true;
    target?: string;
    backlinks?: import('./types').BacklinkEntry[];
    index?: Record<string, import('./types').BacklinkEntry[]>;
    generated_at: string;
  }>(`/tablero/api/v2/wiki-index${qs}`);
}

export function getVaultTree(path = '') {
  const qs = path ? `?path=${encodeURIComponent(path)}` : '';
  return fetchJSON<{
    ok: true;
    path: string;
    children: import('./types').VaultNode[];
  }>(`/tablero/api/v2/vault/tree${qs}`);
}

// P3 fetchers

export interface InfraBadge {
  id: string;
  status: 'ok' | 'warn' | 'error';
  value?: string | number;
  detail?: string;
  link?: string;
  last_check: string;
  crones?: Array<{
    name: string;
    status: 'ok' | 'warn' | 'error';
    last_run?: string;
    expected_interval_s: number;
    detail?: string;
  }>;
}

export function getInfraStatus() {
  return fetchJSON<{ ok: true; generated_at: string; badges: InfraBadge[] }>(
    '/tablero/api/v2/infra/status',
  );
}

export interface AgenteCatalogo {
  slug: string;
  label: string;
  timeout_s: number;
}

export function getAgentesCatalogo() {
  return fetchJSON<{ ok: true; agentes: AgenteCatalogo[] }>('/tablero/api/v2/agentes/catalogo');
}

export function ejecutarAgente(slug: string, timeout_s?: number) {
  return fetchJSON<{
    ok: boolean;
    slug: string;
    output: string;
    duration_s: number;
    triggered_by: string;
    error?: string;
  }>('/tablero/api/v2/agentes/ejecutar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug, timeout_s }),
  });
}

/**
 * Edita una entrada con concurrencia optimista (D-003).
 * `ifMatch` debe ser el concurrency_token de la nota (modified_at o ts).
 * Lanza ConcurrencyError ante 409 stale_modified_at.
 */
export async function editarNota(body: EditarRequest, ifMatch: string): Promise<EditarResponse> {
  try {
    return await fetchJSON<EditarResponse>('/tablero/api/v2/nota', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'If-Match': ifMatch,
      },
      body: JSON.stringify(body),
    });
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      // Re-fetch body para obtener current_modified_at — necesitamos el response body
      // El error ya tiene detalle pero falta current_modified_at; haremos un fetch raw
      const token = getToken();
      const res = await fetch('/tablero/api/v2/nota', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'If-Match': ifMatch,
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });
      const data = (await res.json().catch(() => ({}))) as Partial<StaleModifiedAtError>;
      throw new ConcurrencyError(data.current_modified_at ?? '');
    }
    throw e;
  }
}
