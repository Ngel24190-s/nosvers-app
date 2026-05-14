import { useChannel } from '../../../lib/ws';
import type { RecordatoriosSnapshot } from '../../../lib/api-types';

export default function HoyTab() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  const items = (data?.items ?? []).slice(0, 8);
  return (
    <div className="space-y-3">
      <h2 className="font-display text-xl mb-2">Hoy</h2>
      {items.length === 0 ? (
        <p className="text-muted text-sm">Sin recordatorios pendientes.</p>
      ) : (
        items.map((it) => (
          <div
            key={it.slug}
            className="p-4 bg-bg border border-border rounded-xl"
          >
            <div className="text-xs text-muted mb-1">
              {it.fecha} · {it.autor || '—'} · prioridad {it.prioridad}
            </div>
            <div className="text-fg">{it.texto}</div>
          </div>
        ))
      )}
    </div>
  );
}
