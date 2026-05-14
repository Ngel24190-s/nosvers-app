import { useEffect, useState } from 'react';
import { Dog } from 'lucide-react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Payload {
  nombre?: string;
  proxima_vacuna?: string | null;
  ultimo_paseo?: string | null;
  peso_kg?: number | null;
  animo?: string | null;
  empty?: boolean;
}

export function BrisWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('bris', (p) => setData(p as Payload)), [ws]);

  return (
    <WidgetCard
      title="BRIS"
      icon={<Dog size={14} />}
      accent="violet"
      index={index}
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          <div className="h-6 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
        </div>
      ) : data.empty && !data.nombre ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin datos de Bris
          </span>
        </div>
      ) : (
        <motion.div
          className="flex flex-col gap-2 text-xs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-baseline justify-between">
            <span className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
              vacuna
            </span>
            <span className="cockpit-mono text-[11px] text-cockpit-text">
              {data.proxima_vacuna || '—'}
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
              paseo
            </span>
            <span className="cockpit-mono text-[11px] text-cockpit-text">
              {data.ultimo_paseo || '—'}
            </span>
          </div>
          <div className="flex items-baseline justify-between">
            <span className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
              peso
            </span>
            <span className="cockpit-mono text-[11px] text-cockpit-text">
              {data.peso_kg != null ? `${data.peso_kg} kg` : '—'}
            </span>
          </div>
          {data.animo && (
            <div className="flex items-baseline justify-between">
              <span className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
                ánimo
              </span>
              <span className="cockpit-mono text-[11px] text-accent-violet">
                {data.animo}
              </span>
            </div>
          )}
        </motion.div>
      )}
    </WidgetCard>
  );
}
