/**
 * ViewSwitcher — selector con las 5 vistas del timeline (US4).
 *
 * Persiste la elección en localStorage vía useVistaPersist (FR-012).
 */
import { List, Table, Trello, Calendar, Image } from 'lucide-react';
import { type Vista } from '../lib/types';

interface Props {
  vista: Vista;
  onChange: (v: Vista) => void;
}

const VISTAS_META: { id: Vista; label: string; Icon: typeof List }[] = [
  { id: 'lista', label: 'Lista', Icon: List },
  { id: 'tabla', label: 'Tabla', Icon: Table },
  { id: 'kanban', label: 'Kanban', Icon: Trello },
  { id: 'calendario', label: 'Calendario', Icon: Calendar },
  { id: 'galeria', label: 'Galería', Icon: Image },
];

export function ViewSwitcher({ vista, onChange }: Props) {
  return (
    <div role="tablist" aria-label="Vista del timeline" className="inline-flex rounded-lg border border-tinta/15 bg-cream p-0.5">
      {VISTAS_META.map(({ id, label, Icon }) => (
        <button
          key={id}
          type="button"
          role="tab"
          aria-selected={vista === id}
          onClick={() => onChange(id)}
          className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs transition ${
            vista === id
              ? 'bg-emerald-600 text-white'
              : 'text-tinta/70 hover:bg-tinta/5 hover:text-tinta'
          }`}
          title={label}
        >
          <Icon size={14} aria-hidden />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}
