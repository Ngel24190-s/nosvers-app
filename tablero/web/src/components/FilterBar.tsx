import { useState } from 'react';
import clsx from 'clsx';
import { X } from 'lucide-react';
import { ETIQUETAS, type AutorFiltro, type Etiqueta, type TimelineFilters } from '../lib/types';

interface Props {
  filters: TimelineFilters;
  onChange: (next: TimelineFilters) => void;
}

const AUTORES: { value: AutorFiltro; label: string }[] = [
  { value: 'ambos', label: 'Ambos' },
  { value: 'angel', label: 'Angel' },
  { value: 'africa', label: 'África' },
];

export function FilterBar({ filters, onChange }: Props) {
  const [rangeError, setRangeError] = useState<string | null>(null);

  function update(patch: Partial<TimelineFilters>) {
    const next = { ...filters, ...patch };
    if (next.desde && next.hasta && next.desde > next.hasta) {
      setRangeError('La fecha "hasta" debe ser igual o posterior a "desde".');
      return;
    }
    setRangeError(null);
    onChange(next);
  }

  function clearAll() {
    setRangeError(null);
    onChange({ autor: 'ambos', etiqueta: '', desde: '', hasta: '' });
  }

  const hasActiveFilter = filters.autor !== 'ambos' || filters.etiqueta || filters.desde || filters.hasta;

  return (
    <div className="rounded-2xl border border-tinta/10 bg-white p-3 flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1" role="radiogroup" aria-label="Autor">
        {AUTORES.map((a) => (
          <button
            key={a.value}
            type="button"
            onClick={() => update({ autor: a.value })}
            className={clsx(
              'chip border transition-colors',
              filters.autor === a.value
                ? 'bg-verde text-cream border-verde'
                : 'bg-cream text-tinta/80 border-tinta/15 hover:bg-tinta/5',
            )}
            role="radio"
            aria-checked={filters.autor === a.value}
          >
            {a.label}
          </button>
        ))}
      </div>

      <span className="text-tinta/30">·</span>

      <select
        className="rounded-md border border-tinta/15 bg-cream px-2 py-1 text-sm"
        value={filters.etiqueta}
        onChange={(e) => update({ etiqueta: e.target.value as Etiqueta | '' })}
        aria-label="Etiqueta"
      >
        <option value="">todas las etiquetas</option>
        {ETIQUETAS.map((e) => (
          <option key={e} value={e}>
            #{e}
          </option>
        ))}
      </select>

      <span className="text-tinta/30">·</span>

      <label className="text-sm text-tinta/70">
        desde&nbsp;
        <input
          type="date"
          className="rounded-md border border-tinta/15 bg-cream px-2 py-1 text-sm"
          value={filters.desde}
          onChange={(e) => update({ desde: e.target.value })}
        />
      </label>
      <label className="text-sm text-tinta/70">
        hasta&nbsp;
        <input
          type="date"
          className="rounded-md border border-tinta/15 bg-cream px-2 py-1 text-sm"
          value={filters.hasta}
          onChange={(e) => update({ hasta: e.target.value })}
        />
      </label>

      {hasActiveFilter && (
        <button
          type="button"
          onClick={clearAll}
          className="ml-auto chip border border-tinta/15 hover:bg-tinta/5 text-tinta/70 flex items-center gap-1"
        >
          <X size={12} />
          limpiar filtros
        </button>
      )}

      {rangeError && (
        <p className="basis-full text-sm text-africa">{rangeError}</p>
      )}
    </div>
  );
}
