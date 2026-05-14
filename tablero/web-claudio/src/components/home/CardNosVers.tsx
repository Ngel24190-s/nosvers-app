import { Sprout } from 'lucide-react';
import { useChannel } from '../../lib/ws';
import type { RevenueSnapshot } from '../../lib/api-types';

export default function CardNosVers({ onSelect }: { onSelect: () => void }) {
  const { data } = useChannel<RevenueSnapshot>('revenue');
  const mes = data?.mes_actual_eur ?? 0;
  const pedidos = data?.pedidos_mes ?? 0;
  return (
    <button
      onClick={onSelect}
      className="relative overflow-hidden rounded-2xl p-6 text-left
                 bg-gradient-to-br from-emerald-200 via-lime-200 to-emerald-100
                 border border-emerald-300/60
                 active:scale-[0.99] transition-transform"
      style={{ minHeight: 168 }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-emerald-900 font-display text-2xl">NosVers</div>
          <div className="text-emerald-800/80 text-xs">ferme lombricole</div>
        </div>
        <Sprout size={28} className="text-emerald-900/80" />
      </div>
      <div className="text-emerald-950 text-lg font-medium">
        {mes.toFixed(0)} € mes · {pedidos} pedido{pedidos === 1 ? '' : 's'}
      </div>
    </button>
  );
}
