import { useState } from 'react';
import { Bell, Clock, Plus, CalendarDays } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, ListItem, EmptyState } from '../../widgets';
import type { RecordatoriosSnapshot } from '../../../lib/api-types';

function diasRelativo(fechaIso: string): string {
  if (!fechaIso) return '';
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  const f = new Date(fechaIso);
  f.setHours(0, 0, 0, 0);
  const diff = Math.round((f.getTime() - hoy.getTime()) / 86400000);
  if (diff < 0) return `hace ${-diff} d`;
  if (diff === 0) return 'hoy';
  if (diff === 1) return 'mañana';
  if (diff < 7) return `en ${diff} días`;
  if (diff < 14) return 'la semana que viene';
  if (diff < 31) return `en ${Math.round(diff / 7)} semanas`;
  return `en ${Math.round(diff / 30)} meses`;
}

function WidgetStatsRecordatorios() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  return (
    <Card className="p-4">
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Hoy" value={data?.total_hoy ?? 0} accent="amber" size="md" />
        <Stat label="Semana" value={data?.total_semana ?? 0} accent="primary" size="md" />
        <Stat label="Total" value={data?.total ?? 0} accent="neutral" size="md" />
      </div>
    </Card>
  );
}

function WidgetProximosRecordatorios() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  const items = (data?.items ?? [])
    .filter((it) => !it.hecho)
    .sort((a, b) => a.fecha.localeCompare(b.fecha))
    .slice(0, 12);
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <CalendarDays size={16} className="text-amber-700" />
        Próximos recordatorios
      </h3>
      {items.length === 0 ? (
        <EmptyState Icon={Bell} text="Ningún recordatorio pendiente." />
      ) : (
        <div className="relative">
          <div className="absolute left-4 top-2 bottom-2 w-px bg-border" />
          <div className="space-y-2">
            {items.map((it) => (
              <div key={it.slug} className="relative pl-10">
                <span className="absolute left-3 top-3 w-3 h-3 rounded-full bg-amber-400 border-2 border-white shadow" />
                <ListItem
                  Icon={Clock}
                  title={it.texto}
                  meta={`${diasRelativo(it.fecha)} · ${it.autor || '—'}`}
                  accent={it.prioridad >= 4 ? 'urgent' : 'neutral'}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

function WidgetQuickAddRecordatorio() {
  const [val, setVal] = useState('');
  const submit = () => {
    if (!val.trim()) return;
    console.log('[recordar] añadir', val);
    setVal('');
  };
  return (
    <Card className="p-3">
      <div className="flex gap-2">
        <input
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Recuérdame que…"
          className="flex-1 px-3 py-2.5 rounded-lg bg-white border border-stone-200 text-fg placeholder:text-muted focus:outline-none focus:border-primary"
        />
        <button
          onClick={submit}
          disabled={!val.trim()}
          className="shrink-0 w-11 h-11 rounded-lg bg-primary text-on-primary flex items-center justify-center disabled:opacity-40 active:scale-95 transition-transform"
        >
          <Plus size={20} />
        </button>
      </div>
    </Card>
  );
}

export default function RecordarTab() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Recordar</h2>
      <WidgetStatsRecordatorios />
      <WidgetProximosRecordatorios />
      <WidgetQuickAddRecordatorio />
    </div>
  );
}
