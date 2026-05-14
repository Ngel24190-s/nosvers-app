import { useEffect, useState } from 'react';
import { ShoppingBasket } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Item {
  texto: string;
  autor: string;
  fecha: string;
  urgente: boolean;
}

interface Payload {
  items?: Item[];
  total?: number;
  empty?: boolean;
}

export function ComprasWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('compras', (p) => setData(p as Payload)), [ws]);

  const items = data?.items ?? [];

  return (
    <WidgetCard
      title="COMPRAS"
      icon={<ShoppingBasket size={14} />}
      accent="green"
      index={index}
      headerExtra={
        data && !data.empty ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            {data.total} pendientes
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-5 skeleton rounded" />
          ))}
        </div>
      ) : data.empty || items.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            lista vacía
          </span>
        </div>
      ) : (
        <ul className="flex flex-col gap-1 text-xs overflow-y-auto">
          <AnimatePresence>
            {items.slice(0, 12).map((it, i) => (
              <motion.li
                key={`${it.texto}-${i}`}
                className="flex items-center gap-2 py-0.5"
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <span
                  className={`cockpit-mono text-[10px] ${
                    it.urgente ? 'text-accent-red' : 'text-cockpit-textDim'
                  }`}
                >
                  {it.urgente ? '⚠' : '○'}
                </span>
                <span className="truncate text-cockpit-text flex-1">{it.texto}</span>
                <span className="cockpit-mono text-[9px] text-cockpit-textDim">
                  {it.autor}
                </span>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      )}
    </WidgetCard>
  );
}
