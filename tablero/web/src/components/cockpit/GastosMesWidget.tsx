import { useEffect, useState } from 'react';
import { Wallet, ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Payload {
  mes?: string;
  total_mes_eur?: number;
  total_mes_anterior_eur?: number;
  delta_vs_anterior_eur?: number;
  por_categoria?: Record<string, number>;
  n_apuntes?: number;
  empty?: boolean;
}

function fmtEur(v: number): string {
  return v.toLocaleString('es-ES', { maximumFractionDigits: 0 });
}

export function GastosMesWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<Payload | null>(null);

  useEffect(() => ws.subscribe('gastos', (p) => setData(p as Payload)), [ws]);

  const total = data?.total_mes_eur ?? 0;
  const delta = data?.delta_vs_anterior_eur ?? 0;
  const cats = data?.por_categoria ?? {};
  const catEntries = Object.entries(cats).sort((a, b) => b[1] - a[1]);
  const maxCat = catEntries.length ? catEntries[0][1] : 1;

  return (
    <WidgetCard
      title="GASTOS MES"
      icon={<Wallet size={14} />}
      accent="amber"
      index={index}
      headerExtra={
        data && !data.empty ? (
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            {data.mes} · {data.n_apuntes} apuntes
          </span>
        ) : null
      }
    >
      {data === null ? (
        <div className="flex flex-col gap-3">
          <div className="h-12 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
          <div className="h-4 skeleton rounded" />
        </div>
      ) : data.empty ? (
        <div className="flex items-center justify-center h-full">
          <span className="cockpit-mono text-[10px] text-cockpit-textDim">
            sin gastos este mes ni el anterior
          </span>
        </div>
      ) : (
        <div className="flex flex-col gap-3 h-full">
          <div className="flex items-end justify-between">
            <div>
              <div className="cockpit-mono text-[10px] uppercase text-cockpit-textDim">
                total
              </div>
              <div className="text-2xl font-bold text-accent-amber">
                {fmtEur(total)}€
              </div>
            </div>
            <div className="flex items-center gap-1 cockpit-mono text-[11px]">
              {delta < 0 ? (
                <ArrowDownRight size={14} className="text-accent-green" />
              ) : (
                <ArrowUpRight size={14} className="text-accent-red" />
              )}
              <span className={delta < 0 ? 'text-accent-green' : 'text-accent-red'}>
                {delta >= 0 ? '+' : ''}
                {fmtEur(delta)}€ vs anterior
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-1 overflow-y-auto">
            {catEntries.slice(0, 6).map(([cat, eur]) => (
              <div key={cat} className="flex items-center gap-2 text-xs">
                <span className="w-20 truncate cockpit-mono text-[10px] text-cockpit-textDim">
                  {cat}
                </span>
                <div className="flex-1 h-2 bg-cockpit-border/30 rounded overflow-hidden">
                  <motion.div
                    className="h-full bg-accent-amber/60"
                    initial={{ width: 0 }}
                    animate={{ width: `${(eur / maxCat) * 100}%` }}
                    transition={{ duration: 0.4, ease: 'easeOut' }}
                  />
                </div>
                <span className="cockpit-mono text-[10px] text-cockpit-text w-12 text-right">
                  {fmtEur(eur)}€
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </WidgetCard>
  );
}
