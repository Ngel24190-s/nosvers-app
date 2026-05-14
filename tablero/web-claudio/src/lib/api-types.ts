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

// === 009 — widgets ricos =====================================================

export interface CocheSnapshot {
  matricula?: string;
  modelo?: string;
  kilometros?: number;
  itv_proxima?: string;
  itv_dias_falta?: number | null;
  seguro_renovacion?: string;
  seguro_dias_falta?: number | null;
  ultimo_mantenimiento?: string;
  empty?: boolean;
}

export interface MedicacionItem {
  quien: string;
  medicamento: string;
  hora: string;
  en_minutos: number;
}

export interface MedicacionSnapshot {
  proxima?: MedicacionItem | null;
  hoy?: MedicacionItem[];
  total_activos?: number;
  empty?: boolean;
}

export interface MenuHoyPlato {
  comida?: string;
  cena?: string;
  postre?: string;
}

export interface MenuHoySnapshot {
  dia?: string;
  fecha?: string;
  comida?: string;
  cena?: string;
  postre?: string;
  notas?: string;
  empty?: boolean;
}

export interface BrisSnapshot {
  nombre?: string;
  proxima_vacuna?: string | null;
  ultimo_paseo?: string | null;
  peso_kg?: number | null;
  animo?: string | null;
  ts?: string;
  empty?: boolean;
}

export interface ComprasSnapshot {
  items?: Array<{ texto: string; autor: string; fecha?: string; urgente?: boolean }>;
  total?: number;
  completados_pendientes_archivar?: number;
  empty?: boolean;
}

export interface GastosSnapshot {
  mes?: string;
  total_mes_eur?: number;
  total_mes_anterior_eur?: number;
  delta_vs_anterior_eur?: number;
  por_categoria?: Record<string, number>;
  ultimos?: Array<{ fecha: string; eur: number; concepto: string; categoria: string; autor: string }>;
  n_apuntes?: number;
  presupuesto_mes_eur?: number;
  empty?: boolean;
}

export interface HuertoCultivo {
  nombre: string;
  area_m2?: number;
  siembra?: string;
  cosecha_prev?: string;
  ultimo_riego?: string;
  estado?: 'plantado' | 'creciendo' | 'maduro' | 'cosechado';
}

export interface HuertoSnapshot {
  cultivos?: HuertoCultivo[];
  total_cultivos?: number;
  ultimo_riego_general?: string;
  compost?: {
    nivel: 'bajo' | 'medio' | 'alto';
    temperatura_c?: number;
    ultima_volteada?: string;
  };
  ts?: string;
  empty?: boolean;
}

export interface PedidosStripeSnapshot {
  mes_total_eur?: number;
  pedidos_mes?: number;
  ultimo?: {
    cliente?: string;
    producto?: string;
    eur?: number;
    fecha?: string;
  } | null;
  club_subs?: {
    activos: number;
    nuevos_mes: number;
    mrr_eur: number;
  };
  ts?: string;
  empty?: boolean;
}

export interface AappmaContacto {
  nombre: string;
  rol: string;
  telefono?: string;
  email?: string;
}

export interface AappmaStockSnapshot {
  dendrobaena_disponibles_g?: number;
  dendrobaena_reservadas_g?: number;
  proxima_entrega?: string;
  pedido_activo?: {
    cliente?: string;
    cantidad_g?: number;
    fecha_entrega?: string;
    estado?: string;
  } | null;
  contactos?: AappmaContacto[];
  ts?: string;
  empty?: boolean;
}

export interface ClimaSnapshot {
  ciudad?: string;
  temperatura_c?: number;
  sensacion_c?: number;
  weather_code?: number;
  weather_label?: string;
  viento_kmh?: number;
  precipitacion_mm?: number;
  pronostico?: Array<{ fecha: string; min: number; max: number; code: number }>;
  ts?: string;
  empty?: boolean;
}

export interface ChantierWS {
  slug: string;
  nombre: string;
  cliente: string;
  direccion?: string;
  devis_eur: number;
  estado: 'urgente' | 'en_cours' | 'debut' | 'pausado' | 'archivado';
  fecha_inicio?: string;
  fecha_fin_prev?: string;
  dias_restantes?: number | null;
  equipe_ids?: string[];
}

export interface ChantiersActivosSnapshot {
  total?: number;
  urgentes?: number;
  en_cours?: number;
  debut?: number;
  items?: ChantierWS[];
  ts?: string;
  empty?: boolean;
}

export interface EventoAgenda {
  hora: string;
  chantier: string;
  tipo: 'reunion' | 'visita' | 'livraison' | 'rdv_client' | 'autre';
  descripcion?: string;
  operateurs?: string[];
}

export interface ChantiersAgendaSnapshot {
  fecha?: string;
  eventos?: EventoAgenda[];
  total?: number;
  ts?: string;
  empty?: boolean;
}

export interface OperateurWS {
  id: string;
  nombre: string;
  rol?: string;
  estado: 'actif' | 'formation' | 'absent' | 'conge';
  chantier_actual?: string;
  iniciales?: string;
}

export interface EquipeSnapshot {
  operateurs?: OperateurWS[];
  total?: number;
  actifs?: number;
  en_formation?: number;
  ts?: string;
  empty?: boolean;
}

export interface DocItem {
  tipo: 'ppsps' | 'plan_retrait' | 'devis' | 'certificat' | 'diag_amiante' | 'autre';
  nombre: string;
  chantier?: string;
  size_kb?: number;
  fecha?: string;
}

export interface DocumentosTrabajoSnapshot {
  por_tipo?: Record<string, DocItem[]>;
  total?: number;
  ts?: string;
  empty?: boolean;
}

export interface AgentesSnapshot {
  items?: Array<{
    nombre: string;
    estado: 'ok' | 'error' | 'pausa' | 'desconocido';
    ultima_ejecucion?: string;
    cron?: string;
  }>;
  total_ok?: number;
  total_error?: number;
  ts?: string;
  empty?: boolean;
}

// Canal `agentes` real (vienen del worker `agentes_tick`)
export interface AgenteEstado {
  id: string;
  state: 'idle' | 'running' | 'error' | 'missing';
  last_run_ts: number;
  last_status: string | null;
}

export interface AgentesWorkerSnapshot {
  agentes: AgenteEstado[];
}

// === 010 — NosVers completo ==================================================

export interface BriefingAfricaSnapshot {
  fecha: string;
  titulo: string;
  extracto: string;
  items: Array<{ titulo: string; extracto: string }>;
  ts: string;
}

export interface ProximaPublicacionSnapshot {
  estado: 'en_cola' | 'publicados' | 'vacio';
  siguiente: {
    n: number;
    dia: string;
    hora: string;
    tipo: string;
    caption: string;
    status: string;
  } | null;
  pendientes: number;
  aprobados: number;
  total?: number;
  ts: string;
}

export interface VermiculturaSnapshot {
  eisenia: {
    bacs: number;
    biomasa_kg: number;
    produccion_lombricompost_kg_mes: number;
    ultima_recolte: string;
  };
  dendrobaena: {
    stock_g: number;
    reservadas_g: number;
    proxima_entrega: string;
  };
  aappma: {
    pedido_activo: {
      cliente: string;
      cantidad_g: number;
      fecha_entrega: string;
      estado: string;
    };
    concours_proximo: string;
  };
  thierry: {
    nombre: string;
    rol: string;
    telefono: string;
    email: string;
    ultimo_contacto: string;
  };
  ts: string;
}

export interface ComposteurSnapshot {
  activo: boolean;
  nota: string;
  temperatura_c: number;
  humedad_pct: number;
  fase: string;
  ultima_volteada: string;
  proxima_volteada: string;
  alertas: string[];
  ts: string;
}

export interface TareasDiaSnapshot {
  fecha: string;
  tareas: Array<{
    texto: string;
    categoria: string;
    hecha: boolean;
    prioridad: number;
  }>;
  total: number;
  pendientes: number;
  hechas: number;
  ts: string;
}

export interface EiseniaRunSnapshot {
  ultima_ejecucion: string | null;
  alertas: Array<{
    type: string;
    bac: string;
    jours: number | null;
    kg_estimes: number | null;
    urgence: string;
  }>;
  estado: 'alertas' | 'ok' | 'sin_datos';
  urgentes?: number;
  resumen: string;
  ts: string;
}

export interface WebTrafficSnapshot {
  fuente: string;
  dominio: string;
  rango_dias: number;
  total_visitas: number;
  total_paginas: number;
  visitas_hoy: number;
  visitas_ayer: number;
  delta_dia: number;
  series: Array<{ fecha: string; visitas: number; paginas_vistas: number }>;
  ts: string;
}

export interface SearchConsoleSnapshot {
  fuente: string;
  rango_dias: number;
  total_impresiones: number;
  total_clicks: number;
  ctr_pct: number;
  posicion_media: number;
  queries_top: Array<{ query: string; impresiones: number; clicks: number; posicion_media: number }>;
  series: Array<{ fecha: string; impresiones: number; clicks: number }>;
  ts: string;
}

export interface AhrefsSnapshot {
  fuente: string;
  dominio: string;
  domain_rating: number;
  url_rating: number;
  backlinks: number;
  referring_domains: number;
  organic_keywords: number;
  organic_traffic: number;
  top_backlinks: Array<{ url: string; dr: number; anchor: string }>;
  ts: string;
}

export interface EngagementRedesSnapshot {
  fuente: string;
  rango_dias: number;
  instagram: {
    followers: number;
    posts_semana: number;
    likes_total: number;
    comments_total: number;
    engagement_rate_pct: number;
    agente_logs_semana: number;
  };
  youtube: {
    subs: number;
    videos_semana: number;
    views_semana: number;
    watch_time_min: number;
    agente_logs_semana: number;
  };
  facebook: {
    page_likes: number;
    posts_semana: number;
    reach: number;
    engagements: number;
    agente_logs_semana: number;
  };
  ts: string;
}

export interface ComentariosWpSnapshot {
  fuente: string;
  pendientes: number;
  items: Array<{
    id: number;
    autor: string;
    post: string;
    extracto: string;
    fecha: string;
  }>;
  ts: string;
}

export interface TelegramResumenSnapshot {
  fuente: string;
  total: number;
  items: Array<{ ts: string; autor: string; texto: string }>;
  ts: string;
}

export interface LogsErroresSnapshot {
  fuente: string;
  total_errores: number;
  ventana_horas: number;
  por_agente: Record<string, { n: number; ultimo: string; mtime: number }>;
  ts: string;
}
