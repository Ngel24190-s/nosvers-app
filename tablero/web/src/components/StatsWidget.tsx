/**
 * StatsWidget — actividad client-side derivada del timeline ya cargado (US9).
 *
 * FR-039: cálculos en cliente, no requiere endpoint adicional.
 * D-009: agrupación diaria en TZ Europe/Madrid.
 */
import { useMemo } from 'react';
import type { TimelineEntry } from '../lib/types';

interface Props {
  entradas: TimelineEntry[];
}

function fechaLocal(ts: string): string {
  try {
    const d = new Date(ts);
    return new Intl.DateTimeFormat('es-ES', {
      timeZone: 'Europe/Madrid',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(d);
  } catch {
    return '?';
  }
}

function isThisWeek(ts: string): boolean {
  try {
    const d = new Date(ts);
    const now = new Date();
    const monday = new Date(now);
    const day = (now.getDay() + 6) % 7; // 0 = lunes
    monday.setDate(now.getDate() - day);
    monday.setHours(0, 0, 0, 0);
    return d >= monday;
  } catch {
    return false;
  }
}

export function StatsWidget({ entradas }: Props) {
  const stats = useMemo(() => {
    const porAutorSemana: Record<string, number> = { angel: 0, africa: 0 };
    const etiquetasContador = new Map<string, number>();
    const ultimos30: Record<string, number> = {};

    const hace30 = new Date();
    hace30.setDate(hace30.getDate() - 30);

    for (const e of entradas) {
      if (isThisWeek(e.ts)) {
        porAutorSemana[e.autor] = (porAutorSemana[e.autor] ?? 0) + 1;
        etiquetasContador.set(e.etiqueta, (etiquetasContador.get(e.etiqueta) ?? 0) + 1);
      }
      const fecha = fechaLocal(e.ts);
      try {
        const d = new Date(e.ts);
        if (d >= hace30) {
          ultimos30[fecha] = (ultimos30[fecha] ?? 0) + 1;
        }
      } catch {
        // skip
      }
    }

    const top10 = [...etiquetasContador.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);

    const sparkline = [];
    for (let i = 29; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const fecha = new Intl.DateTimeFormat('es-ES', {
        timeZone: 'Europe/Madrid',
        year: 'numeric', month: '2-digit', day: '2-digit',
      }).format(d);
      sparkline.push({ fecha, count: ultimos30[fecha] ?? 0 });
    }

    return { porAutorSemana, top10, sparkline };
  }, [entradas]);

  const totalSemana = stats.porAutorSemana.angel + stats.porAutorSemana.africa;
  const maxSpark = Math.max(1, ...stats.sparkline.map((s) => s.count));

  if (entradas.length === 0) {
    return (
      <div className="rounded border border-tinta/10 bg-cream/40 p-3 text-center text-sm text-tinta/50">
        Sin datos. Captura una nota con Ctrl+N.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      <div className="rounded border border-tinta/10 bg-white p-3">
        <h3 className="mb-2 text-xs font-medium uppercase text-tinta/60">Esta semana</h3>
        {(['angel', 'africa'] as const).map((autor) => {
          const n = stats.porAutorSemana[autor];
          const pct = totalSemana > 0 ? (n / totalSemana) * 100 : 0;
          return (
            <div key={autor} className="mb-2">
              <div className="mb-0.5 flex justify-between text-xs">
                <span className="capitalize">{autor}</span>
                <span className="font-mono text-tinta/60">{n}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-tinta/10">
                <div
                  className={`h-full ${autor === 'angel' ? 'bg-emerald-600' : 'bg-amber-600'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="rounded border border-tinta/10 bg-white p-3">
        <h3 className="mb-2 text-xs font-medium uppercase text-tinta/60">Etiquetas top</h3>
        <ul className="space-y-1">
          {stats.top10.map(([etiqueta, count]) => (
            <li key={etiqueta} className="flex items-center justify-between text-xs">
              <span className="capitalize">{etiqueta}</span>
              <span className="font-mono text-tinta/60">×{count}</span>
            </li>
          ))}
          {stats.top10.length === 0 && (
            <li className="text-xs text-tinta/40">Sin etiquetas esta semana</li>
          )}
        </ul>
      </div>

      <div className="rounded border border-tinta/10 bg-white p-3">
        <h3 className="mb-2 text-xs font-medium uppercase text-tinta/60">Últimos 30 días</h3>
        <div className="flex h-12 items-end gap-0.5">
          {stats.sparkline.map((s, i) => (
            <div
              key={i}
              className="flex-1 bg-emerald-500/60"
              style={{ height: `${(s.count / maxSpark) * 100}%` }}
              title={`${s.fecha}: ${s.count}`}
            />
          ))}
        </div>
        <p className="mt-1 text-[10px] text-tinta/40">
          Total: {stats.sparkline.reduce((a, b) => a + b.count, 0)}
        </p>
      </div>
    </div>
  );
}
