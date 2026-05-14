import { Home } from 'lucide-react';
import { useChannel } from '../../lib/ws';
import type { RecordatoriosSnapshot } from '../../lib/api-types';

export default function CardCasa({ onSelect }: { onSelect: () => void }) {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  const hoy = data?.total_hoy ?? 0;
  return (
    <button
      onClick={onSelect}
      className="relative overflow-hidden rounded-2xl p-6 text-left
                 bg-gradient-to-br from-amber-200 via-orange-200 to-amber-100
                 border border-amber-300/60
                 active:scale-[0.99] transition-transform"
      style={{ minHeight: 168 }}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-amber-900 font-display text-2xl">Casa</div>
          <div className="text-amber-800/80 text-xs">vida familiar</div>
        </div>
        <Home size={28} className="text-amber-900/80" />
      </div>
      <div className="text-amber-950 text-lg font-medium">
        {hoy === 0 ? 'sin nada pendiente hoy' : `${hoy} cosas hoy`}
      </div>
    </button>
  );
}
