import { useEffect, useMemo } from 'react';
import { X, Archive } from 'lucide-react';
import type { NoteFull } from '../lib/types';
import { AuthorChip } from './AuthorChip';
import { TagChip } from './TagChip';
import { MarkdownBody } from '../lib/markdown';
import { formatDateES, formatTimeES } from '../lib/format';
import { BacklinksPanel } from './BacklinksPanel';

interface Props {
  nota: NoteFull | null;
  onClose: () => void;
  onArchive?: () => void;
}

function slugForBacklinks(path: string): string {
  // path es "dia/2026-05-13.md#<ts>"; slug = ts (D-002 a nivel de entrada)
  if (path.includes('#')) {
    return path.split('#', 2)[1] ?? '';
  }
  // fallback al filename
  const last = path.split('/').pop() ?? '';
  return last.replace(/\.md$/, '');
}

export function NoteDetail({ nota, onClose, onArchive }: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (nota) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [nota, onClose]);

  const slug = useMemo(() => (nota ? slugForBacklinks(nota.path) : ''), [nota]);

  if (!nota) return null;

  const { frontmatter, body_markdown, attachments } = nota;
  const autor = (frontmatter.autor ?? 'desconocido') as 'angel' | 'africa' | 'desconocido';
  const etiqueta = frontmatter.etiqueta;
  const ts = frontmatter.ts ?? '';

  return (
    <div className="fixed inset-0 z-50 flex">
      <div
        className="absolute inset-0 bg-tinta/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside className="relative ml-auto h-full w-full sm:max-w-2xl bg-cream shadow-2xl overflow-y-auto">
        <header className="sticky top-0 z-10 bg-cream/95 backdrop-blur border-b border-tinta/10 px-4 py-3 flex items-center gap-2">
          <AuthorChip autor={autor} />
          <span className="text-sm text-tinta/70">
            {ts ? formatDateES(ts) : ''} {ts && <span className="text-tinta/40">· {formatTimeES(ts)}</span>}
          </span>
          {etiqueta && (
            <span className="ml-2">
              <TagChip etiqueta={etiqueta} />
            </span>
          )}
          <span className="ml-auto flex items-center gap-1">
            {onArchive && (
              <button
                type="button"
                onClick={onArchive}
                aria-label="archivar"
                title="Archivar nota"
                className="rounded-full p-1.5 text-amber-700 hover:bg-amber-50"
              >
                <Archive size={16} />
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              aria-label="cerrar"
              className="rounded-full p-1.5 text-tinta/60 hover:bg-tinta/5 hover:text-tinta"
            >
              <X size={18} />
            </button>
          </span>
        </header>

        <section className="px-4 py-3">
          <h4 className="text-xs uppercase tracking-wide text-tinta/40">Metadatos</h4>
          <dl className="mt-1 grid grid-cols-[max-content_1fr] gap-x-3 gap-y-0.5 text-sm">
            {Object.entries(frontmatter).map(([k, v]) =>
              v === null || v === undefined || v === '' ? null : (
                <div key={k} className="contents">
                  <dt className="text-tinta/50">{k}</dt>
                  <dd className="text-tinta/80 break-all">{String(v)}</dd>
                </div>
              ),
            )}
          </dl>
        </section>

        <hr className="mx-4 border-tinta/10" />

        <section className="px-4 py-4">
          <MarkdownBody body={body_markdown} attachments={attachments} />
        </section>

        {slug && (
          <section className="px-4 pb-4">
            <BacklinksPanel slug={slug} />
          </section>
        )}
      </aside>
    </div>
  );
}
