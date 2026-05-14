import { useChannel } from '../../../lib/ws';
import type { RevenueSnapshot } from '../../../lib/api-types';

export default function HoyGranja() {
  const { data } = useChannel<RevenueSnapshot>('revenue');
  const mes = data?.mes_actual_eur ?? 0;
  const ant = data?.mes_anterior_eur ?? 0;
  const delta = mes - ant;
  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl">Granja · hoy</h2>
      <div className="p-5 bg-bg border border-border rounded-2xl">
        <div className="text-xs text-muted">Mes actual</div>
        <div className="font-mono text-4xl text-primary mt-1">
          {mes.toFixed(0)} €
        </div>
        <div className={`text-sm mt-1 ${delta >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
          {delta >= 0 ? '+' : ''}{delta.toFixed(0)} € vs mes anterior
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 bg-bg border border-border rounded-lg">
          <div className="text-xs text-muted">Pedidos</div>
          <div className="font-mono text-2xl">{data?.pedidos_mes ?? 0}</div>
        </div>
        <div className="p-3 bg-bg border border-border rounded-lg">
          <div className="text-xs text-muted">Mes anterior</div>
          <div className="font-mono text-2xl">{ant.toFixed(0)} €</div>
        </div>
      </div>
    </div>
  );
}
