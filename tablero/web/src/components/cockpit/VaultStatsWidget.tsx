import { Database } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { BarList, DonutChart } from '@tremor/react';
import { WidgetCard } from './WidgetCard';
import { getTimeline } from '../../lib/api';
import { DEFAULT_FILTERS } from '../../lib/types';

interface TimelineEntry {
  fecha: string;
  ts: string;
  autor: string;
  etiquetas?: string[];
}

export function VaultStatsWidget({ index }: { index: number }) {
  const [items, setItems] = useState<TimelineEntry[]>([]);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const data = await getTimeline(DEFAULT_FILTERS);
        if (alive) setItems((data.entradas as TimelineEntry[]) ?? []);
      } catch {
        /* ignore */
      }
    };
    load();
    const t = setInterval(load, 60_000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  const stats = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    const weekAgo = Date.now() - 7 * 86_400_000;
    let hoy = 0;
    let semana = 0;
    const tagCount = new Map<string, number>();
    const autorCount = new Map<string, number>();
    for (const it of items) {
      if (it.fecha === today) hoy++;
      const ts = new Date(it.ts).getTime();
      if (!isNaN(ts) && ts >= weekAgo) semana++;
      for (const t of it.etiquetas ?? []) tagCount.set(t, (tagCount.get(t) ?? 0) + 1);
      if (it.autor) autorCount.set(it.autor, (autorCount.get(it.autor) ?? 0) + 1);
    }
    const top5 = Array.from(tagCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, value]) => ({ name, value }));
    const donutData = Array.from(autorCount.entries()).map(([name, value]) => ({ name, value }));
    return { hoy, semana, top5, donutData };
  }, [items]);

  return (
    <WidgetCard
      title="Vault"
      icon={<Database size={14} />}
      accent="green"
      index={index}
      headerExtra={
        <span className="cockpit-mono text-[10px] text-cockpit-textDim">
          {items.length} notas
        </span>
      }
    >
      <div className="flex flex-col h-full gap-2">
        <div className="grid grid-cols-2 gap-2">
          <div className="cockpit-glass !shadow-none border-cockpit-border bg-cockpit-panelHi/40 rounded-md p-2">
            <div className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim">hoy</div>
            <div className="cockpit-mono text-2xl font-bold text-accent-green">{stats.hoy}</div>
          </div>
          <div className="cockpit-glass !shadow-none border-cockpit-border bg-cockpit-panelHi/40 rounded-md p-2">
            <div className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim">semana</div>
            <div className="cockpit-mono text-2xl font-bold text-accent-cyan">{stats.semana}</div>
          </div>
        </div>
        <div className="flex-1 min-h-0 overflow-hidden">
          <div className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim mb-1">
            etiquetas top
          </div>
          {stats.top5.length > 0 ? (
            <BarList
              data={stats.top5}
              color="emerald"
              className="text-[11px]"
              showAnimation
            />
          ) : (
            <div className="cockpit-mono text-[10px] text-cockpit-textDim italic">sin datos</div>
          )}
        </div>
        {stats.donutData.length > 0 && (
          <div className="h-12 flex items-center justify-center">
            <DonutChart
              data={stats.donutData}
              category="value"
              index="name"
              colors={['emerald', 'orange']}
              showLabel={false}
              showAnimation
              className="h-12 w-12"
            />
            <div className="ml-2 cockpit-mono text-[10px] text-cockpit-textDim">
              {stats.donutData.map((d) => `${d.name}:${d.value}`).join(' · ')}
            </div>
          </div>
        )}
      </div>
    </WidgetCard>
  );
}
