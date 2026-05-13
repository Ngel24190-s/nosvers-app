// Hand-written TypeScript types mirroring contracts/*.openapi.yaml + data-model.md.
// Keep in sync with the OpenAPI files.

export type Autor = 'angel' | 'africa';
export type AutorFiltro = Autor | 'ambos';
export type Etiqueta = 'trabajo' | 'nosvers' | 'familia' | 'mental' | 'idea' | 'otro';
export type Origen = 'voz_movil' | 'voz_linux' | 'texto_directo' | 'otro';

export const ETIQUETAS: readonly Etiqueta[] = [
  'trabajo', 'nosvers', 'familia', 'mental', 'idea', 'otro',
] as const;

export interface TimelineEntry {
  path: string;
  fecha: string;       // YYYY-MM-DD
  ts: string;          // ISO 8601
  autor: Autor;
  etiqueta: Etiqueta;
  origen?: Origen;
  titulo: string | null;
  preview: string;
  tiene_audio: boolean;
  metadata_incompleta: boolean;
}

export interface TimelineResponse {
  ok: true;
  entradas: TimelineEntry[];
  total: number;
  rango: { desde: string; hasta: string };
}

export interface SearchHit {
  fecha: string;
  ts: string;
  autor: Autor;
  etiqueta: Etiqueta;
  origen?: Origen;
  fragmento: string;
}

export interface SearchResponse {
  ok: true;
  query: string;
  filtro_autor: Autor | null;
  rango: { desde: string; hasta: string };
  total: number;
  resultados: SearchHit[];
}

export interface NoteFull {
  path: string;
  frontmatter: {
    ts?: string;
    autor?: Autor;
    etiqueta?: Etiqueta;
    origen?: Origen;
    audio?: string | null;
    clasificador_confianza?: number;
    clasificador_modelo?: string;
    [k: string]: unknown;
  };
  body_markdown: string;
  mtime: string;
  attachments: { src: string; exists: boolean; kind: 'image' | 'audio' | 'other' }[];
}

export interface NoteResponse {
  ok: true;
  nota: NoteFull;
}

export interface Identity {
  sub: Autor;
  device: string;
  jti: string;
  exp: number;
}

export interface WhoamiResponse {
  ok: true;
  identidad: Identity;
}

export interface ErrorResponse {
  ok: false;
  error: string;
  detalle?: string;
}

export interface TimelineFilters {
  autor: AutorFiltro;
  etiqueta: Etiqueta | '';
  desde: string;       // YYYY-MM-DD or ''
  hasta: string;       // YYYY-MM-DD or ''
}

export const DEFAULT_FILTERS: TimelineFilters = {
  autor: 'ambos',
  etiqueta: '',
  desde: '',
  hasta: '',
};

// ─── Fase B+C types ──────────────────────────────────────────────────────────

/** Vista activa del timeline (FR-010, FR-012). */
export type Vista = 'lista' | 'tabla' | 'kanban' | 'calendario' | 'galeria';

export const VISTAS: readonly Vista[] = ['lista', 'tabla', 'kanban', 'calendario', 'galeria'] as const;

/** Borrador de captura persistido en localStorage (FR-003). */
export interface BorradorCaptura {
  titulo: string;
  cuerpo: string;
  etiquetas: Etiqueta[];
  savedAt: string;
}

/** Response de POST /tablero/api/v2/capturar (US1). */
export interface CapturarResponse {
  ok: true;
  path: string;              // "dia/<fecha>.md#<ts>"
  fecha: string;             // YYYY-MM-DD
  ts: string;                // ISO 8601
  autor: Autor;
  etiqueta: Etiqueta;
  concurrency_token: string;
}

/** Response de PATCH /tablero/api/v2/nota (US2). */
export interface EditarResponse {
  ok: true;
  path: string;
  fecha: string;
  ts: string;
  autor: Autor;
  etiqueta: Etiqueta;
  concurrency_token: string;
  modified_at: string;
}

/** Body para POST /tablero/api/v2/capturar (US1). */
export interface CapturarRequest {
  titulo?: string;
  cuerpo: string;
  etiquetas?: Etiqueta[];
}

/** Body para PATCH /tablero/api/v2/nota (US2). */
export interface EditarRequest {
  path: string;              // "dia/<fecha>.md#<ts>"
  cuerpo?: string;
  titulo?: string;
  etiqueta?: Etiqueta;
}

/** Error 409 stale_modified_at — propagado como ConcurrencyError. */
export interface StaleModifiedAtError {
  ok: false;
  error: 'stale_modified_at';
  current_modified_at: string;
}

// Proyectos (US6 — futuro)
export interface Proyecto {
  slug: string;
  titulo: string;
  estado: 'todo' | 'doing' | 'done' | 'blocked' | 'sin_estado';
  modified_at: string;
  responsable?: Autor;
  deadline?: string;
  etiquetas?: string[];
  cuerpo?: string;
}

// Vault tree (US8 — futuro)
export interface VaultNode {
  name: string;
  type: 'folder' | 'file';
  size?: number;
  modified_at?: string;
}

// Wiki-index (US7 — futuro)
export interface BacklinkEntry {
  source_slug: string;
  source_path: string;
  source_autor?: Autor;
  source_modified_at?: string;
  context: string;
}
