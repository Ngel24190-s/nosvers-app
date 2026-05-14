import { Bot, Shield, Server, Brain, BugOff } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import NeuralGraph from '../../NeuralGraph';
import { WidgetAgenteCard } from '../widgets';
import type {
  AgentesWorkerSnapshot,
  LogsErroresSnapshot,
} from '../../../lib/api-types';

const AGENTES_LISTA = [
  'orchestrator',
  'agt00_intelligence',
  'agt01_visual',
  'agt02_instagram',
  'agt04_seo',
  'agt05_africa',
  'agt06_infoproduct',
  'agt07_diario',
  'agt07_youtube',
  'agt08_facebook',
  'agt_infra',
  'agt_eisenia',
  'agt_analyste',
  'agt_directeur',
];

interface HealthSnapshot {
  cpu_pct?: number;
  mem_pct?: number;
  disk_pct?: number;
  uptime_s?: number;
  load1?: number;
}

interface AegisSnapshot {
  alertas?: Array<{ tipo: string; severidad: string; mensaje: string; ts: string }>;
  total?: number;
  ultimo?: string;
}

function WidgetListaAgentes() {
  const { data } = useChannel<AgentesWorkerSnapshot>('agentes');
  const byName = new Map((data?.agentes ?? []).map((a) => [a.id, a]));
  const runningCount = AGENTES_LISTA.filter((n) => byName.get(n)?.state === 'running').length;
  const errorCount = AGENTES_LISTA.filter((n) => byName.get(n)?.state === 'error').length;
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Bot size={16} className="text-emerald-700" />
          Plantilla · 14 agentes
        </h3>
        <span className="text-[11px] text-muted">
          {runningCount} running · {errorCount} error
        </span>
      </div>
      <div className="space-y-1.5">
        {AGENTES_LISTA.map((n) => (
          <WidgetAgenteCard key={n} nombre={n} estado={byName.get(n)} />
        ))}
      </div>
    </Card>
  );
}

function WidgetAEGISAlerts() {
  const { data } = useChannel<AegisSnapshot>('aegis');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Shield size={16} className="text-emerald-700" />
        AEGIS · alertas seguridad
      </h3>
      {!data || (data.alertas?.length ?? 0) === 0 ? (
        <EmptyState text="Sin alertas recientes." />
      ) : (
        <div className="space-y-1.5">
          {data.alertas!.slice(0, 4).map((a, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5 border-b border-emerald-100 last:border-0">
              <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full flex-shrink-0 ${
                a.severidad === 'critico' || a.severidad === 'alta'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-amber-100 text-amber-800'
              }`}>
                {a.severidad}
              </span>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-fg leading-snug">{a.mensaje}</div>
                <div className="text-[11px] text-muted">{a.tipo} · {a.ts}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetServiciosVPS() {
  const { data } = useChannel<HealthSnapshot>('health');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Server size={16} className="text-emerald-700" />
          Servicios VPS
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Server size={16} className="text-emerald-700" />
        Servicios VPS
      </h3>
      <div className="grid grid-cols-3 gap-3">
        <Stat
          label="CPU"
          value={`${(data.cpu_pct ?? 0).toFixed(0)}%`}
          accent={(data.cpu_pct ?? 0) > 80 ? 'amber' : 'emerald'}
          size="sm"
        />
        <Stat
          label="RAM"
          value={`${(data.mem_pct ?? 0).toFixed(0)}%`}
          accent={(data.mem_pct ?? 0) > 85 ? 'amber' : 'emerald'}
          size="sm"
        />
        <Stat
          label="Disco"
          value={`${(data.disk_pct ?? 0).toFixed(0)}%`}
          accent={(data.disk_pct ?? 0) > 90 ? 'amber' : 'emerald'}
          size="sm"
        />
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-[11px] text-muted">
        <div>Load: <span className="text-fg">{(data.load1 ?? 0).toFixed(2)}</span></div>
        <div>Uptime: <span className="text-fg">
          {data.uptime_s ? `${Math.floor(data.uptime_s / 86400)}d` : '—'}
        </span></div>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-[11px]">
        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Caddy</div>
        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> MCP</div>
        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> dev_server</div>
        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500" /> agents</div>
      </div>
    </Card>
  );
}

function WidgetNeuralGraphMini() {
  return (
    <Card className="p-4 flex flex-col items-center">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3 self-start">
        <Brain size={16} className="text-emerald-700" />
        Red neuronal · agentes
      </h3>
      <NeuralGraph color="#5A7A2E" />
      <div className="mt-2 text-[11px] text-muted text-center">
        Visualización del cluster · pulsa cuando un agente piensa
      </div>
    </Card>
  );
}

function WidgetLogsErrores() {
  const { data } = useChannel<LogsErroresSnapshot>('logs_errores');
  const entries = data ? Object.entries(data.por_agente) : [];
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <BugOff size={16} className="text-emerald-700" />
          Errores · 24h
        </h3>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
          {data?.total_errores ?? 0}
        </span>
      </div>
      {entries.length === 0 ? (
        <EmptyState text="Sin errores · todo limpio." />
      ) : (
        <div className="space-y-1.5">
          {entries.slice(0, 6).map(([agente, info]) => (
            <div key={agente} className="py-1.5 border-b border-emerald-100 last:border-0">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-fg">{agente}</span>
                <span className="text-[10px] uppercase px-1.5 py-0.5 rounded-full bg-red-100 text-red-800">
                  {info.n}
                </span>
              </div>
              {info.ultimo && (
                <div className="text-[11px] text-muted mt-0.5 truncate">{info.ultimo}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function Agentes() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg flex items-center gap-2">
        <Bot size={22} className="text-emerald-700" />
        Agentes
      </h2>
      <WidgetListaAgentes />
      <WidgetAEGISAlerts />
      <WidgetServiciosVPS />
      <WidgetNeuralGraphMini />
      <WidgetLogsErrores />
    </div>
  );
}
