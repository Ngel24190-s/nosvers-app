import { useChannel } from '../../../lib/ws';
import type { RecordatoriosSnapshot } from '../../../lib/api-types';

export default function RecordarTab() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  return (
    <div className="space-y-3">
      <h2 className="font-display text-xl mb-2">Próximos recordatorios</h2>
      <div className="text-muted text-sm">
        {data?.total_semana ?? 0} esta semana · {data?.total ?? 0} en total
      </div>
      {(data?.items ?? []).map((it) => (
        <div key={it.slug} className="p-3 bg-bg border border-border rounded-lg">
          <div className="text-xs text-muted">
            {it.fecha} · {it.autor}
          </div>
          <div>{it.texto}</div>
        </div>
      ))}
    </div>
  );
}
