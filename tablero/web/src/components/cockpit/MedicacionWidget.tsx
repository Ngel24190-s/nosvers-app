import { useEffect, useState } from 'react';
import { Pill } from 'lucide-react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Proxima {
  quien: string;
  medicamento: string;
  dosis: string;
  hora: string;
  minutos_hasta: number;
}

interface Cita {
  fecha: string;
  quien: string;
  especialista: string;
}

interface Payload {
  proxima?: Proxima | null;
  n_items_activos?: number;
  proximas_citas?: Cita[];
  empty?: boolean;
}

export function MedicacionWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('medicacion', (p) => setData(p as Payload)), [ws]);

  const proxima = data?.proxima ?? null;
  const proximoMin = proxima?.minutos_hasta ?? Infinity;
  const urgente = proximoMin <= 30;

  return (
    <WidgetCard
      title="MEDICACIÓN"
      icon={<Pill size={14} />}
      accent={urgente ? 'amber' : 'green'}
      index={index}
      critical={urgente}
      headerExtra={
        data?.n_items_activos ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            {data.n_items_activos} pautas
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          <div className="h-10 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
        </div>
      ) : data.empty ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin pautas activas
          </span>
        </div>
      ) : (
        <div className="flex flex-col gap-2 h-full">
          {proxima ? (
            <motion.div
              className="flex flex-col gap-1"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <div className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
                próxima toma
              </div>
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-lg font-bold ${urgente ? 'text-accent-amber animate-pulse' : 'text-cockpit-text'}`}
                >
                  {proxima.hora}
                </span>
                <span className="cockpit-mono text-[10px] text-cockpit-textDim">
                  ({proxima.minutos_hasta}m)
                </span>
              </div>
              <div className="text-xs text-cockpit-text truncate">
                {proxima.quien}: {proxima.medicamento}
              </div>
              {proxima.dosis && (
                <div className="cockpit-mono text-[10px] text-cockpit-textDim">
                  {proxima.dosis}
                </div>
              )}
            </motion.div>
          ) : (
            <div className="cockpit-mono text-[10px] text-cockpit-textDim">
              sin tomas próximas
            </div>
          )}

          {data.proximas_citas && data.proximas_citas.length > 0 && (
            <div className="mt-auto border-t border-cockpit-border/30 pt-1">
              <div className="cockpit-mono text-[9px] uppercase text-cockpit-textDim mb-0.5">
                citas
              </div>
              <ul className="text-[10px] cockpit-mono">
                {data.proximas_citas.slice(0, 2).map((c, i) => (
                  <li key={i} className="truncate text-cockpit-textDim">
                    {c.fecha} · {c.quien} → {c.especialista}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </WidgetCard>
  );
}
