import { useChannel } from '../../../lib/ws';
import type { RevenueSnapshot } from '../../../lib/api-types';

export default function Tienda() {
  const { data } = useChannel<RevenueSnapshot>('revenue');
  return (
    <div className="space-y-4">
      <h2 className="font-display text-2xl">Tienda · Stripe</h2>
      <div className="p-5 bg-bg border border-border rounded-2xl">
        <div className="text-xs text-muted">Ingresos mes actual</div>
        <div className="font-mono text-4xl text-primary mt-1">
          {(data?.mes_actual_eur ?? 0).toFixed(2)} €
        </div>
      </div>
      <div className="p-4 bg-bg border border-border rounded-xl">
        <div className="text-xs text-muted mb-1">Pedidos del mes</div>
        <div className="font-mono text-2xl">{data?.pedidos_mes ?? 0}</div>
      </div>
    </div>
  );
}
