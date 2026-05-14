// Tipos compartidos con backend Python. Escrito a mano (clarify D11).

export interface ChantierResumen {
  slug: string;
  nombre: string;
  cliente: string;
  direccion?: string;
  devis_eur: number;
  fecha_inicio: string;
  fecha_fin_prev: string;
  estado: 'activo' | 'archivado' | 'urgente' | 'pausado';
  equipe_ids: string[];
}

export interface ChantierDetail extends ChantierResumen {
  journal_recientes: Array<{ fecha: string; extracto: string }>;
}

export interface OperateurResumen {
  id: string;
  nombre?: string;
  rol?: string;
  activo?: string;
}

export interface DocumentoResumen {
  tipo: string;
  nombre: string;
  size: number;
  mtime: number;
}

export interface DictadoResponse {
  ok: boolean;
  error?: string;
  detalle?: string;
  intent?: {
    tool: string;
    args: Record<string, unknown>;
    confidence: number;
    fallback: boolean;
    cached: boolean;
  };
  tool_result?: string;
  voice_response?: {
    text: string;
    audio_url?: string;
  };
  latency_ms?: number;
}

export interface TrabajoSnapshot {
  chantiers_activos: number;
  activos?: Array<{ slug: string; nombre: string; cliente: string }>;
  alertas?: Array<{ chantier: string; tipo: string; fecha: string }>;
  ultimo_evento?: { chantier: string; tipo: string; descripcion: string; fecha: string } | null;
  equipe_disponible?: number;
  ts?: string;
  empty?: boolean;
}

export interface RecordatoriosSnapshot {
  items?: Array<{
    slug: string;
    texto: string;
    fecha: string;
    autor: string;
    prioridad: number;
    hecho: boolean;
  }>;
  total_hoy?: number;
  total_semana?: number;
  total?: number;
  empty?: boolean;
}

export interface RevenueSnapshot {
  mes_actual_eur?: number;
  mes_anterior_eur?: number;
  pedidos_mes?: number;
  ts?: string;
  empty?: boolean;
}
