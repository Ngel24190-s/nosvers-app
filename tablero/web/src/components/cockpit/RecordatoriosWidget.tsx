import { useEffect, useState } from 'react';
import { Bell } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Item {
  slug: string;
  texto: string;
  fecha: string;
  autor: string;
  prioridad: number;
  hecho: boolean;
}

interface Payload {
  items?: Item[];
  total_hoy?: number;
  total_semana?: number;
  total?: number;
  empty?: boolean;
}

function dayLabel(iso: string): string {
  if (!iso) return '';
  try {
    const f = new Date(iso + 'T00:00:00');
    const hoy = new Date();
    hoy.setHours(0, 0, 0, 0);
    const dt = Math.round((f.getTime() - hoy.getTime()) / 86400000);
    if (dt === 0) return 'hoy';
    if (dt === 1) return 'mañana';
    if (dt < 0) return `hace ${-dt}d`;
    if (dt < 7) return `+${dt}d`;
    return iso.slice(5);
  } catch {
    return iso;
  }
}

function prioColor(p: number): string {
  if (p >= 8) return 'text-accent-red';
  if (p >= 5) return 'text-accent-orange';
  return 'text-accent-green';
}

export function RecordatoriosWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('recordatorios', (p) => setData(p as Payload)), [ws]);

  const items = (data?.items ?? []).slice(0, 8);
  const hoy = data?.total_hoy ?? 0;
  const semana = data?.total_semana ?? 0;

  return (
    <WidgetCard
      title="RECORDATORIOS"
      icon={<Bell size={14} />}
      accent="amber"
      index={index}
      headerExtra={
        data && !data.empty ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            {hoy} hoy · {semana} semana
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-6 skeleton rounded" />
          ))}
        </div>
      ) : data.empty || items.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin recordatorios pendientes
          </span>
        </div>
      ) : (
        <ul className="flex flex-col gap-1 text-xs">
          <AnimatePresence>
            {items.map((it) => (
              <motion.li
                key={it.slug}
                className="flex items-center justify-between gap-2 py-1 border-b border-cockpit-border/30 last:border-0"
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <span className={`cockpit-mono text-[10px] ${prioColor(it.prioridad)}`}>
                    ●
                  </span>
                  <span className="truncate text-cockpit-text">{it.texto}</span>
                </div>
                <span className="cockpit-mono text-[10px] text-cockpit-textDim shrink-0">
                  {dayLabel(it.fecha)}
                </span>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </WidgetCard>
  );
}
