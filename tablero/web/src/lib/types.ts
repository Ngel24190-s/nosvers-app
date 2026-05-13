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
