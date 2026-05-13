import type { TimelineEntry } from '../lib/types';
import { AuthorChip } from './AuthorChip';
import { TagChip } from './TagChip';
import { formatDateES, formatTimeES } from '../lib/format';
import { Mic } from 'lucide-react';

interface Props {
  entry: TimelineEntry;
  onSelect: (entry: TimelineEntry) => void;
  snippet?: string;
}

function Snippet({ html }: { html: string }) {
  // Allowlist: only <mark>…</mark> tags. Split-and-render manually to avoid dangerouslySetInnerHTML.
  const parts = html.split(/(<mark>.*?<\/mark>)/g);
  return (
    <p className="mt-1 text-sm text-tinta/70 leading-relaxed">
      {parts.map((p, i) => {
        const m = p.match(/^<mark>(.*?)<\/mark>$/);
        if (m) return <mark key={i}>{m[1]}</mark>;
        return <span key={i}>{p}</span>;
      })}
    </p>
  );
}

export function TimelineItem({ entry, onSelect, snippet }: Props) {
  return (
    <button
      type="button"
      onClick={() => onSelect(entry)}
      className="card w-full text-left p-4 hover:bg-tinta/5 focus:outline-none focus:ring-2 focus:ring-verde"
    >
      <div className="flex items-center gap-2">
        <AuthorChip autor={entry.autor} />
        <span className="text-xs text-tinta/60">{formatDateES(entry.fecha)}</span>
        <span className="text-xs text-tinta/40">·</span>
        <span className="text-xs text-tinta/40">{formatTimeES(entry.ts)}</span>
        {entry.tiene_audio && (
          <span className="ml-auto text-tinta/40" aria-label="contiene audio">
            <Mic size={14} />
          </span>
        )}
      </div>
      <h3 className="mt-1 font-display text-lg leading-snug">
        {entry.titulo ?? <span className="text-tinta/40 italic">Sin título</span>}
      </h3>
      {snippet ? (
        <Snippet html={snippet} />
      ) : (
        entry.preview && (
          <p className="mt-1 text-sm text-tinta/70 leading-relaxed line-clamp-2">{entry.preview}</p>
        )
      )}
      {entry.etiqueta && (
        <div className="mt-2 flex flex-wrap gap-1">
          <TagChip etiqueta={entry.etiqueta} />
        </div>
      )}
    </button>
  );
}
