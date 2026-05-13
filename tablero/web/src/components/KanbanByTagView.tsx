/**
 * KanbanByTagView — kanban por etiqueta (US4).
 *
 * 6 columnas fijas (5 etiquetas Fase A + 'sin etiqueta'). Cada nota aparece
 * en la columna correspondiente a su etiqueta. Notas multi-etiqueta replicadas
 * con badge "1 de N" — pero la realidad Fase A es 1 etiqueta por nota, así que
 * el caso multi solo aplica si el frontmatter inline tuviera etiquetas: [...].
 */
import { useMemo } from 'react';
import { type Etiqueta, ETIQUETAS, type TimelineEntry } from '../lib/types';
import { AuthorChip } from './AuthorChip';
import { formatDateES } from '../lib/format';

interface Props {
  entradas: TimelineEntry[];
  onSelect: (e: TimelineEntry) => void;
}

const COLUMNAS: (Etiqueta | 'sin_etiqueta')[] = [...ETIQUETAS, 'sin_etiqueta'];

const LABELS: Record<Etiqueta | 'sin_etiqueta', string> = {
  trabajo: 'Trabajo',
  nosvers: 'NosVers',
  familia: 'Familia',
  mental: 'Mental',
  idea: 'Ideas',
  otro: 'Otro',
  sin_etiqueta: 'Sin etiqueta',
};

export function KanbanByTagView({ entradas, onSelect }: Props) {
  const agrupadas = useMemo(() => {
    const m = new Map<string, TimelineEntry[]>();
    for (const col of COLUMNAS) m.set(col, []);
    for (const e of entradas) {
      const k = e.etiqueta || 'sin_etiqueta';
      m.get(k)?.push(e);
    }
    return m;
  }, [entradas]);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
      {COLUMNAS.map((col) => {
        const items = agrupadas.get(col) ?? [];
        return (
          <div key={col} className="rounded-md border border-tinta/10 bg-cream/40 p-2">
            <h3 className="mb-2 flex items-center justify-between text-xs font-medium uppercase text-tinta/60">
              <span>{LABELS[col]}</span>
              <span className="rounded-full bg-tinta/10 px-1.5 text-[10px]">{items.length}</span>
            </h3>
            <ul className="space-y-1.5">
              {items.map((e) => (
                <li key={e.path}>
                  <button
                    type="button"
                    onClick={() => onSelect(e)}
                    className="w-full rounded border border-tinta/10 bg-white p-2 text-left text-xs hover:border-emerald-400 hover:shadow-sm"
                  >
                    <div className="mb-1 flex items-center justify-between gap-1">
                      <AuthorChip autor={e.autor} />
                      <time className="text-[10px] text-tinta/50">{formatDateES(e.ts)}</time>
                    </div>
                    <p className="line-clamp-3 text-tinta">{e.titulo ?? e.preview}</p>
                  </button>
                </li>
              ))}
              {items.length === 0 && (
                <li className="px-2 py-3 text-center text-[10px] text-tinta/40">vacío</li>
              )}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
