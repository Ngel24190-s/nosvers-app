/**
 * CalendarMonthView — vista calendario mensual del timeline (US4).
 *
 * Muestra el mes actual con conteo de notas por día. Clic en un día filtra
 * el timeline (vía callback onSelectDay).
 */
import { useMemo, useState } from 'react';
import type { TimelineEntry } from '../lib/types';

interface Props {
  entradas: TimelineEntry[];
  onSelectDay: (fecha: string) => void;
}

const DOW_LABELS = ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'];

function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

export function CalendarMonthView({ entradas, onSelectDay }: Props) {
  const today = useMemo(() => new Date(), []);
  const [mes, setMes] = useState<Date>(startOfMonth(today));

  const counts = useMemo(() => {
    const m = new Map<string, number>();
    for (const e of entradas) {
      m.set(e.fecha, (m.get(e.fecha) ?? 0) + 1);
    }
    return m;
  }, [entradas]);

  const grid = useMemo(() => {
    const first = mes;
    const dayOfWeek = (first.getDay() + 6) % 7; // 0 = lunes
    const start = new Date(first);
    start.setDate(first.getDate() - dayOfWeek);
    const cells: Date[] = [];
    for (let i = 0; i < 42; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      cells.push(d);
    }
    return cells;
  }, [mes]);

  const mesLabel = mes.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
  const monthIdx = mes.getMonth();

  function iso(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  return (
    <div className="rounded border border-tinta/10 bg-cream/40 p-3">
      <header className="mb-2 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setMes(addMonths(mes, -1))}
          className="rounded px-2 py-1 text-sm text-tinta/70 hover:bg-tinta/5"
        >
          ←
        </button>
        <h3 className="text-sm font-medium capitalize text-tinta">{mesLabel}</h3>
        <button
          type="button"
          onClick={() => setMes(addMonths(mes, 1))}
          className="rounded px-2 py-1 text-sm text-tinta/70 hover:bg-tinta/5"
        >
          →
        </button>
      </header>

      <div className="mb-1 grid grid-cols-7 gap-1 text-center text-[10px] uppercase text-tinta/50">
        {DOW_LABELS.map((l) => <div key={l}>{l}</div>)}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {grid.map((d, i) => {
          const fecha = iso(d);
          const inMonth = d.getMonth() === monthIdx;
          const count = counts.get(fecha) ?? 0;
          const isToday = fecha === iso(today);
          return (
            <button
              key={i}
              type="button"
              onClick={() => onSelectDay(fecha)}
              disabled={!inMonth}
              className={`flex h-12 flex-col items-center justify-center rounded text-xs transition ${
                !inMonth ? 'opacity-30' :
                count > 0 ? 'bg-emerald-100 text-emerald-900 hover:bg-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-200' :
                'bg-white/40 text-tinta/60 hover:bg-tinta/5'
              } ${isToday ? 'ring-2 ring-emerald-500' : ''}`}
            >
              <span className="font-medium">{d.getDate()}</span>
              {count > 0 && (
                <span className="mt-0.5 rounded-full bg-emerald-600 px-1.5 text-[9px] leading-tight text-white">
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
