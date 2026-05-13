/**
 * GalleryView — vista galería de cards (US4).
 *
 * Cards con thumbnail si la nota referencia una imagen (`![](attachments/...)`)
 * — placeholder con primera línea si no hay imagen.
 */
import type { TimelineEntry } from '../lib/types';
import { AuthorChip } from './AuthorChip';
import { TagChip } from './TagChip';
import { formatDateES } from '../lib/format';

interface Props {
  entradas: TimelineEntry[];
  onSelect: (e: TimelineEntry) => void;
}

// Regex para detectar imagen markdown en la preview
const IMG_RE = /!\[[^\]]*\]\(([^)]+)\)/;

function extractImage(preview: string): string | null {
  const m = preview.match(IMG_RE);
  return m ? m[1] : null;
}

export function GalleryView({ entradas, onSelect }: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {entradas.map((e) => {
        const img = extractImage(e.preview);
        return (
          <button
            key={e.path}
            type="button"
            onClick={() => onSelect(e)}
            className="overflow-hidden rounded-lg border border-tinta/10 bg-white text-left transition hover:border-emerald-400 hover:shadow-md"
          >
            {img ? (
              <div className="aspect-video bg-tinta/5">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img} alt="" className="h-full w-full object-cover" loading="lazy" />
              </div>
            ) : (
              <div className="flex aspect-video items-center justify-center bg-gradient-to-br from-emerald-50 to-tinta/5 p-3">
                <p className="line-clamp-3 text-center text-sm text-tinta/70">{e.preview}</p>
              </div>
            )}
            <div className="space-y-1 p-3">
              <div className="flex items-center justify-between gap-2">
                <AuthorChip autor={e.autor} />
                <TagChip etiqueta={e.etiqueta} />
              </div>
              <p className="line-clamp-2 text-sm font-medium text-tinta">
                {e.titulo ?? e.preview}
              </p>
              <time className="text-[10px] text-tinta/50">{formatDateES(e.ts)}</time>
            </div>
          </button>
        );
      })}
      {entradas.length === 0 && (
        <div className="col-span-full px-3 py-12 text-center text-sm text-tinta/50">
          Sin entradas que mostrar.
        </div>
      )}
    </div>
  );
}
