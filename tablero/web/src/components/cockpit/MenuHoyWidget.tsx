import { useEffect, useState } from 'react';
import { UtensilsCrossed } from 'lucide-react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Payload {
  dia?: string;
  fecha?: string;
  comida?: string;
  cena?: string;
  raw?: string;
  empty?: boolean;
}

export function MenuHoyWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('menu_dia', (p) => setData(p as Payload)), [ws]);

  return (
    <WidgetCard
      title="MENÚ HOY"
      icon={<UtensilsCrossed size={14} />}
      accent="orange"
      index={index}
      headerExtra={
        data && !data.empty ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim capitalize">
            {data.dia}
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          <div className="h-6 skeleton rounded" />
          <div className="h-6 skeleton rounded" />
        </div>
      ) : data.empty ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin menú para hoy
          </span>
        </div>
      ) : (
        <motion.div
          className="flex flex-col gap-2 text-xs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {data.comida && (
            <div>
              <div className="cockpit-mono text-[9px] uppercase text-cockpit-textDim">
                comida
              </div>
              <div className="text-cockpit-text">{data.comida}</div>
            </div>
          )}
          {data.cena && (
            <div>
              <div className="cockpit-mono text-[9px] uppercase text-cockpit-textDim">
                cena
              </div>
              <div className="text-cockpit-text">{data.cena}</div>
            </div>
          )}
          {!data.comida && !data.cena && data.raw && (
            <pre className="cockpit-mono text-[10px] text-cockpit-textDim whitespace-pre-wrap leading-tight">
              {data.raw}
            </pre>
          )}
        </motion.div>
      )}
    </WidgetCard>
  );
}
