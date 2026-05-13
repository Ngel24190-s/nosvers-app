/**
 * TableView — vista tabla del timeline (US4).
 *
 * Columnas: fecha, autor, etiqueta, primera línea. Ordenable por columna.
 */
import { useMemo, useState } from 'react';
import type { TimelineEntry } from '../lib/types';
import { AuthorChip } from './AuthorChip';
import { TagChip } from './TagChip';
import { formatDateES, formatTimeES } from '../lib/format';

interface Props {
  entradas: TimelineEntry[];
  onSelect: (e: TimelineEntry) => void;
}

type SortKey = 'fecha' | 'autor' | 'etiqueta' | 'titulo';
type SortDir = 'asc' | 'desc';

export function TableView({ entradas, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('fecha');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const ordenadas = useMemo(() => {
    const arr = [...entradas];
    arr.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case 'fecha': cmp = a.ts.localeCompare(b.ts); break;
        case 'autor': cmp = a.autor.localeCompare(b.autor); break;
        case 'etiqueta': cmp = a.etiqueta.localeCompare(b.etiqueta); break;
        case 'titulo': cmp = (a.titulo ?? a.preview).localeCompare(b.titulo ?? b.preview); break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [entradas, sortKey, sortDir]);

  function toggleSort(k: SortKey) {
    if (k === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(k);
      setSortDir('desc');
    }
  }

  function arrow(k: SortKey) {
    if (k !== sortKey) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-tinta/15 text-left text-xs uppercase text-tinta/50">
          <tr>
            <th className="cursor-pointer px-3 py-2" onClick={() => toggleSort('fecha')}>
              Fecha{arrow('fecha')}
            </th>
            <th className="cursor-pointer px-3 py-2" onClick={() => toggleSort('autor')}>
              Autor{arrow('autor')}
            </th>
            <th className="cursor-pointer px-3 py-2" onClick={() => toggleSort('etiqueta')}>
              Etiqueta{arrow('etiqueta')}
            </th>
            <th className="cursor-pointer px-3 py-2" onClick={() => toggleSort('titulo')}>
              Título / Preview{arrow('titulo')}
            </th>
          </tr>
        </thead>
        <tbody>
          {ordenadas.map((e) => (
            <tr
              key={e.path}
              onClick={() => onSelect(e)}
              className="cursor-pointer border-b border-tinta/5 hover:bg-tinta/5"
            >
              <td className="whitespace-nowrap px-3 py-2 text-tinta/70">
                {formatDateES(e.ts)} <span className="text-tinta/40">{formatTimeES(e.ts)}</span>
              </td>
              <td className="px-3 py-2"><AuthorChip autor={e.autor} /></td>
              <td className="px-3 py-2"><TagChip etiqueta={e.etiqueta} /></td>
              <td className="px-3 py-2 text-tinta">
                {e.titulo ?? <span className="text-tinta/60">{e.preview}</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {ordenadas.length === 0 && (
        <div className="px-3 py-8 text-center text-sm text-tinta/50">Sin entradas en la vista.</div>
      )}
    </div>
  );
}
