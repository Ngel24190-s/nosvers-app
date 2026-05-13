import { Workflow } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface AgentNode {
  id: string;
  state: 'idle' | 'running' | 'error' | 'missing';
  last_run_ts: number;
  last_status: string | null;
}

const stateColor: Record<AgentNode['state'], string> = {
  idle: 'bg-cockpit-panelHi border-cockpit-border text-cockpit-textDim',
  running: 'bg-accent-orange/20 border-accent-orange text-accent-orange',
  error: 'bg-accent-red/20 border-accent-red text-accent-red',
  missing: 'bg-cockpit-panelHi border-dashed border-cockpit-border text-cockpit-dim',
};

function fmtRel(ts: number): string {
  if (!ts) return '—';
  const d = Date.now() / 1000 - ts;
  if (d < 60) return `${Math.floor(d)}s`;
  if (d < 3600) return `${Math.floor(d / 60)}m`;
  if (d < 86400) return `${Math.floor(d / 3600)}h`;
  return `${Math.floor(d / 86400)}d`;
}

export function AgentesStatusWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [agentes, setAgentes] = useState<AgentNode[]>([]);

  useEffect(
    () =>
      ws.subscribe('agentes', (p) => {
        const payload = p as { agentes: AgentNode[] };
        setAgentes(payload.agentes ?? []);
      }),
    [ws],
  );

  const total = agentes.length;
  const running = agentes.filter((a) => a.state === 'running').length;
  const errors = agentes.filter((a) => a.state === 'error').length;

  return (
    <WidgetCard
      title="Agentes"
      icon={<Workflow size={14} />}
      accent="violet"
      index={index}
      headerExtra={
        <span className="cockpit-mono text-[10px] text-cockpit-textDim">
          {running}▶ · {errors}⚠ · {total}
        </span>
      }
    >
      <div className="grid grid-cols-2 gap-1.5 h-full overflow-y-auto cockpit-scrollbar pr-1">
        {agentes.map((a) => (
          <motion.div
            key={a.id}
            className={`relative rounded-md border px-2 py-1.5 text-[10px] ${stateColor[a.state]}`}
            animate={a.state === 'running' ? { scale: [1, 1.03, 1] } : { scale: 1 }}
            transition={{ duration: 1.4, repeat: a.state === 'running' ? Infinity : 0 }}
          >
            <div className="cockpit-mono font-semibold truncate">{a.id.replace(/^agt_?/, '')}</div>
            <div className="cockpit-mono text-[9px] opacity-70">{fmtRel(a.last_run_ts)}</div>
            {a.state === 'running' && (
              <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-accent-orange animate-pulse-led" />
            )}
          </motion.div>
        ))}
        {total === 0 && (
          <div className="col-span-2 cockpit-mono text-[10px] text-cockpit-textDim italic">
            sin agentes detectados
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
