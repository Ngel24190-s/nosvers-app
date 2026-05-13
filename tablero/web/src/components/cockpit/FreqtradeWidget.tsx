import { TrendingUp, Lock } from 'lucide-react';
import { useEffect, useState } from 'react';
import { WidgetCard } from './WidgetCard';

interface FreqStatus {
  profit_today_eur?: number;
  open_trades?: number;
  closed_trades_today?: number;
  available?: boolean;
}

// El API de Freqtrade vive en otro proceso (puerto 8080 típicamente, protegido).
// El cockpit no tiene credenciales por defecto → placeholder.
// Si se expone vía nginx en /freqtrade/api/v1/... con basic-auth tras el JWT,
// se puede activar luego.
export function FreqtradeWidget({ index }: { index: number }) {
  const [data] = useState<FreqStatus | null>(null);

  useEffect(() => {
    // Por ahora no llamamos — el endpoint no está expuesto al frontend.
    // En cuanto Angel exponga /tablero/api/v2/freqtrade, activar aquí.
  }, []);

  if (!data) {
    return (
      <WidgetCard
        title="Freqtrade"
        icon={<TrendingUp size={14} />}
        accent="amber"
        index={index}
      >
        <div className="flex flex-col items-center justify-center h-full text-center gap-3 px-2">
          <div className="relative">
            <TrendingUp size={32} className="text-cockpit-dim" />
            <Lock
              size={12}
              className="absolute -bottom-1 -right-1 text-accent-orange bg-cockpit-panel rounded-full p-0.5"
            />
          </div>
          <div>
            <div className="cockpit-mono text-[10px] uppercase tracking-wider text-cockpit-textDim">
              API NO EXPUESTA
            </div>
            <p className="text-[10px] text-cockpit-dim mt-1 leading-relaxed">
              Configurar /tablero/api/v2/freqtrade
            </p>
          </div>
        </div>
      </WidgetCard>
    );
  }

  const pnl = data.profit_today_eur ?? 0;
  return (
    <WidgetCard title="Freqtrade" icon={<TrendingUp size={14} />} accent="amber" index={index}>
      <div className="flex flex-col h-full justify-between">
        <div>
          <div className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim">
            PnL hoy
          </div>
          <div
            className="cockpit-mono text-3xl font-bold"
            style={{ color: pnl >= 0 ? '#34d399' : '#ef4444' }}
          >
            {pnl >= 0 ? '+' : ''}€{pnl.toFixed(2)}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 cockpit-mono text-[10px] text-cockpit-textDim">
          <div>
            <div className="text-[9px] uppercase">open</div>
            <div className="text-base font-semibold text-cockpit-text">{data.open_trades ?? 0}</div>
          </div>
          <div>
            <div className="text-[9px] uppercase">closed</div>
            <div className="text-base font-semibold text-cockpit-text">
              {data.closed_trades_today ?? 0}
            </div>
          </div>
        </div>
      </div>
    </WidgetCard>
  );
}
