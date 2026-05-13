import { Euro, Lock } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface RevenuePayload {
  day_eur: number;
  month_eur: number;
  target_eur: number;
  blocked: boolean;
  last_payment: { amount_eur: number; desc: string; ts: number } | null;
}

function useCountUp(value: number, duration = 600) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const from = display;
    const loop = (t: number) => {
      const k = Math.min((t - start) / duration, 1);
      setDisplay(from + (value - from) * (1 - Math.pow(1 - k, 3)));
      if (k < 1) raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);
  return display;
}

export function RevenueWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<RevenuePayload | null>(null);

  useEffect(() => ws.subscribe('revenue', (p) => setData(p as RevenuePayload)), [ws]);

  const month = useCountUp(data?.month_eur ?? 0);
  const target = data?.target_eur ?? 600;
  const pct = Math.min((month / target) * 100, 100);

  if (data?.blocked) {
    return (
      <WidgetCard title="Revenue" icon={<Euro size={14} />} accent="orange" index={index}>
        <div className="flex flex-col items-center justify-center h-full text-center gap-2">
          <Lock size={20} className="text-cockpit-dim" />
          <span className="cockpit-mono text-[10px] text-cockpit-textDim leading-relaxed">
            BLOCKED_OAUTH_HUMAN
          </span>
          <span className="text-[10px] text-cockpit-dim leading-relaxed px-2">
            Configurar STRIPE_SECRET_KEY en .env
          </span>
        </div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard
      title="Revenue"
      icon={<Euro size={14} />}
      accent="orange"
      index={index}
      headerExtra={
        <span className="cockpit-mono text-[10px] text-cockpit-textDim">
          hoy €{(data?.day_eur ?? 0).toFixed(0)}
        </span>
      }
    >
      <div className="flex flex-col h-full justify-between">
        {data === null ? (
          <div className="flex-1 flex flex-col gap-3 p-2">
            <div className="h-10 skeleton rounded" />
            <div className="h-3 skeleton rounded w-2/3" />
            <div className="h-2 skeleton rounded" />
          </div>
        ) : (
          <>
            <div>
              <div className="cockpit-mono text-3xl font-bold text-accent-orange" title={`mes €${data.month_eur.toFixed(2)} · hoy €${data.day_eur.toFixed(2)}`}>
                €{month.toFixed(0)}
              </div>
              <div className="cockpit-mono text-[10px] text-cockpit-textDim mt-1">
                mes · objetivo €{target.toFixed(0)}
              </div>
            </div>
            <div>
              <div className="relative h-2 bg-cockpit-panelHi rounded-full overflow-hidden" title={`${pct.toFixed(1)}% del objetivo`}>
                <motion.div
                  className="absolute inset-y-0 left-0 bg-gradient-to-r from-accent-orange to-accent-amber"
                  style={{ boxShadow: '0 0 12px rgba(251, 146, 60, 0.6)' }}
                  initial={{ width: 0 }}
                  animate={{ width: `${pct}%` }}
                  transition={{ duration: 0.6, ease: 'easeOut' }}
                />
              </div>
              <div className="flex justify-between mt-1 cockpit-mono text-[9px] text-cockpit-textDim">
                <span>{pct.toFixed(0)}%</span>
                {data.last_payment && (
                  <span className="truncate ml-2" title={data.last_payment.desc}>últ. €{data.last_payment.amount_eur.toFixed(0)}</span>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </WidgetCard>
  );
}
