import { useEffect, useState } from 'react';
import { Car } from 'lucide-react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Payload {
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

function diasColor(d: number | null | undefined): string {
  if (d == null) return 'text-cockpit-textDim';
  if (d < 30) return 'text-accent-red';
  if (d < 90) return 'text-accent-amber';
  return 'text-accent-green';
}

export function CocheStatusWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('coche', (p) => setData(p as Payload)), [ws]);

  return (
    <WidgetCard
      title="COCHE"
      icon={<Car size={14} />}
      accent="cyan"
      index={index}
      headerExtra={
        data && !data.empty ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            {data.matricula}
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          <div className="h-6 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
        </div>
      ) : data.empty ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin datos del coche
          </span>
        </div>
      ) : (
        <motion.div
          className="flex flex-col gap-2 text-xs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <div>
            <div className="text-cockpit-text font-semibold truncate">
              {data.modelo || '—'}
            </div>
            {data.kilometros ? (
              <div className="cockpit-mono text-[10px] text-cockpit-textDim">
                {data.kilometros.toLocaleString('es-ES')} km
              </div>
            ) : null}
          </div>

          <div className="flex flex-col gap-1 border-t border-cockpit-border/30 pt-1">
            <div className="flex justify-between items-baseline">
              <span className="cockpit-mono text-[10px] text-cockpit-textDim">ITV</span>
              <span className={`cockpit-mono text-[11px] ${diasColor(data.itv_dias_falta)}`}>
                {data.itv_proxima || '—'}{' '}
                {data.itv_dias_falta != null && `(${data.itv_dias_falta}d)`}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="cockpit-mono text-[10px] text-cockpit-textDim">seguro</span>
              <span className={`cockpit-mono text-[11px] ${diasColor(data.seguro_dias_falta)}`}>
                {data.seguro_renovacion || '—'}{' '}
                {data.seguro_dias_falta != null && `(${data.seguro_dias_falta}d)`}
              </span>
            </div>
            {data.ultimo_mantenimiento && (
              <div className="flex justify-between items-baseline">
                <span className="cockpit-mono text-[10px] text-cockpit-textDim">mant.</span>
                <span className="cockpit-mono text-[11px] text-cockpit-text">
                  {data.ultimo_mantenimiento}
                </span>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </WidgetCard>
  );
}
