/**
 * BacklinksPanel — sección "Referenciada desde" al pie del detail (US7).
 */
import { useEffect, useState } from 'react';
import { Link2 } from 'lucide-react';
import { getWikiIndex } from '../lib/api';
import type { BacklinkEntry } from '../lib/types';

interface Props {
  slug: string;
}

export function BacklinksPanel({ slug }: Props) {
  const [backlinks, setBacklinks] = useState<BacklinkEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      setLoading(true);
      try {
        const r = await getWikiIndex(slug);
        if (!cancelled) setBacklinks(r.backlinks ?? []);
      } catch {
        if (!cancelled) setBacklinks([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return <div className="text-xs text-tinta/40">Cargando referencias…</div>;
  }
  if (backlinks.length === 0) {
    return null;
  }

  return (
    <section className="mt-4 rounded border border-tinta/10 bg-cream/40 p-3">
      <h4 className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase text-tinta/60">
        <Link2 size={12} />
        Referenciada desde ({backlinks.length})
      </h4>
      <ul className="space-y-1.5">
        {backlinks.map((b) => (
          <li key={b.source_path} className="rounded border border-tinta/5 bg-white p-2 text-xs">
            <div className="mb-0.5 flex items-center gap-2 text-tinta/60">
              {b.source_autor && <span className="font-medium">{b.source_autor}</span>}
              <code className="font-mono text-tinta/40">{b.source_path}</code>
            </div>
            <p className="line-clamp-2 text-tinta">{b.context}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
