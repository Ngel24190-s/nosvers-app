import { Server, Bot, Activity } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import NeuralGraph from '../../NeuralGraph';
import type { AgentesSnapshot } from '../../../lib/api-types';

interface HealthSnap {
  cpu_percent?: number;
  mem_percent?: number;
  disk_percent?: number;
  uptime_s?: number;
  empty?: boolean;
}

function fmtUptime(s: number): string {
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  if (d > 0) return `${d}d ${h}h`;
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

function WidgetServiciosVPS() {
  const { data } = useChannel<HealthSnap>('health');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Server size={16} className="text-emerald-700" />
        Servicios VPS
      </h3>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="CPU" value={`${(data?.cpu_percent ?? 0).toFixed(0)}%`} accent="emerald" size="sm" />
        <Stat label="RAM" value={`${(data?.mem_percent ?? 0).toFixed(0)}%`} accent="emerald" size="sm" />
        <Stat label="Disco" value={`${(data?.disk_percent ?? 0).toFixed(0)}%`} accent="emerald" size="sm" />
      </div>
      {data?.uptime_s != null && (
        <div className="mt-3 text-xs text-muted text-center">
          Uptime: <span className="text-fg">{fmtUptime(data.uptime_s)}</span>
        </div>
      )}
    </Card>
  );
}

function WidgetAgentesEstado() {
  const { data } = useChannel<AgentesSnapshot>('agentes');
  const items = data?.items ?? [];
  if (items.length === 0) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Bot size={16} className="text-emerald-700" />
          Agentes
        </h3>
        <EmptyState text="Sin datos de agentes." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Bot size={16} className="text-emerald-700" />
          Agentes
        </h3>
        <span className="text-xs text-muted">
          {data?.total_ok ?? 0} OK · {data?.total_error ?? 0} err
        </span>
      </div>
      <div className="space-y-1">
        {items.slice(0, 8).map((a) => (
          <div key={a.nombre} className="flex items-center justify-between py-1.5 border-b border-emerald-100 last:border-0">
            <div className="min-w-0 flex-1">
              <div className="text-fg text-sm truncate">{a.nombre}</div>
              {a.ultima_ejecucion && (
                <div className="text-xs text-muted">{a.ultima_ejecucion}</div>
              )}
            </div>
            <span className={`shrink-0 w-2.5 h-2.5 rounded-full ${
              a.estado === 'ok' ? 'bg-emerald-500' :
              a.estado === 'error' ? 'bg-red-500' :
              a.estado === 'pausa' ? 'bg-amber-500' :
              'bg-stone-300'
            }`} />
          </div>
        ))}
      </div>
    </Card>
  );
}

function WidgetNeuralGraphMini() {
  return (
    <Card className="p-4 flex flex-col items-center">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-2 self-start">
        <Activity size={16} className="text-emerald-700" />
        Red neuronal
      </h3>
      <div style={{ width: 200, height: 100 }}>
        <NeuralGraph color="#5A7A2E" />
      </div>
      <a
        href="https://tablero.72.61.160.108.nip.io"
        className="mt-2 text-xs text-emerald-700 underline"
      >
        cockpit completo →
      </a>
    </Card>
  );
}

export default function CockpitMini() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Cockpit · mini</h2>
      <WidgetServiciosVPS />
      <WidgetAgentesEstado />
      <WidgetNeuralGraphMini />
    </div>
  );
}
