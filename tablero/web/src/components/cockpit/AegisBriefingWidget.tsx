import { ShieldAlert, AlertTriangle, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Briefing {
  path: string;
  ts: number;
  level: 'info' | 'warn' | 'warning' | 'critical';
  summary: string;
}

interface AegisPayload {
  last_briefing: Briefing | null;
  alerts_active: { id: string; level: string; msg: string }[];
}

function fmtRel(ts: number): string {
  if (!ts) return '—';
  const d = Date.now() / 1000 - ts;
  if (d < 60) return 'ahora';
  if (d < 3600) return `${Math.floor(d / 60)}m`;
  if (d < 86400) return `${Math.floor(d / 3600)}h`;
  return `${Math.floor(d / 86400)}d`;
}

const levelChip: Record<Briefing['level'], string> = {
  info: 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/40',
  warn: 'bg-accent-amber/20 text-accent-amber border-accent-amber/40',
  warning: 'bg-accent-amber/20 text-accent-amber border-accent-amber/40',
  critical: 'bg-accent-red/20 text-accent-red border-accent-red/40',
};

export function AegisBriefingWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<AegisPayload | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => ws.subscribe('aegis', (p) => setData(p as AegisPayload)), [ws]);

  const briefing = data?.last_briefing;
  const isCritical = briefing?.level === 'critical' || (data?.alerts_active.length ?? 0) > 0;

  return (
    <>
      <WidgetCard
        title="AEGIS"
        icon={<ShieldAlert size={14} />}
        accent={isCritical ? 'red' : 'violet'}
        index={index}
        critical={isCritical}
      >
        <div className="flex flex-col h-full justify-between">
          {briefing ? (
            <>
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <span
                    className={`cockpit-mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${levelChip[briefing.level]}`}
                  >
                    {briefing.level}
                  </span>
                  <span className="cockpit-mono text-[10px] text-cockpit-textDim">
                    {fmtRel(briefing.ts)}
                  </span>
                </div>
                <p className="text-xs text-cockpit-text leading-relaxed line-clamp-4">
                  {briefing.summary}
                </p>
              </div>
              <button
                onClick={() => setOpen(true)}
                className="cockpit-mono text-[10px] text-accent-violet hover:text-accent-green transition self-start"
              >
                ver completo →
              </button>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center gap-2">
              <AlertTriangle size={20} className="text-cockpit-dim" />
              <span className="cockpit-mono text-[10px] text-cockpit-textDim">Sin alertas</span>
            </div>
          )}
        </div>
      </WidgetCard>
      <AnimatePresence>
        {open && briefing && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          >
            <motion.div
              className="cockpit-glass max-w-2xl w-full p-6"
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="cockpit-mono text-[10px] uppercase tracking-wider text-accent-violet">
                    AEGIS Briefing · {briefing.path}
                  </div>
                  <h2 className="text-lg font-semibold text-cockpit-text mt-1">
                    Nivel {briefing.level}
                  </h2>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="text-cockpit-textDim hover:text-cockpit-text"
                  aria-label="cerrar"
                >
                  <X size={18} />
                </button>
              </div>
              <p className="text-sm text-cockpit-text leading-relaxed whitespace-pre-wrap">
                {briefing.summary}
              </p>
              <div className="mt-4 cockpit-mono text-[10px] text-cockpit-textDim">
                Para ver el .md completo: abrir desde Obsidian o el sidebar del Dashboard.
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
