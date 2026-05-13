/**
 * PapeleraView — lista de notas archivadas con restauración (US3).
 *
 * Lee directamente knowledge_base/dia/archivo/ via getVaultTree.
 */
import { useCallback, useEffect, useState } from 'react';
import { Archive, ArrowUp } from 'lucide-react';
import { getVaultTree, restaurarNota } from '../lib/api';
import type { VaultNode } from '../lib/types';

interface Props {
  onRestaurada?: () => void;
}

export function PapeleraView({ onRestaurada }: Props) {
  const [archivos, setArchivos] = useState<VaultNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getVaultTree('dia/archivo');
      setArchivos(r.children.filter((c) => c.type === 'file').sort((a, b) =>
        (b.modified_at ?? '').localeCompare(a.modified_at ?? ''),
      ));
    } catch (e) {
      // 404 si no hay carpeta archivo/ todavía
      if (String(e).includes('404')) {
        setArchivos([]);
      } else {
        setError(String(e));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  async function restaurar(name: string) {
    try {
      await restaurarNota(`dia/archivo/${name}`);
      await cargar();
      onRestaurada?.();
    } catch (e) {
      setError(String(e));
    }
  }

  if (loading) {
    return (
      <div className="px-3 py-8 text-center text-sm text-tinta/50">Cargando papelera…</div>
    );
  }
  if (error) {
    return <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">{error}</div>;
  }
  if (archivos.length === 0) {
    return (
      <div className="rounded border border-tinta/10 bg-cream/40 px-3 py-8 text-center text-sm text-tinta/50">
        <Archive size={28} className="mx-auto mb-2 text-tinta/30" />
        Papelera vacía. Las notas archivadas aparecen aquí.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="font-display text-lg">Papelera</h2>
      <ul className="divide-y divide-tinta/5 rounded border border-tinta/10 bg-white">
        {archivos.map((f) => (
          <li key={f.name} className="flex items-center justify-between px-3 py-2 text-sm">
            <div>
              <span className="font-mono text-tinta">{f.name}</span>
              {f.modified_at && (
                <time className="ml-2 text-xs text-tinta/50">{f.modified_at.slice(0, 10)}</time>
              )}
            </div>
            <button
              type="button"
              onClick={() => restaurar(f.name)}
              className="inline-flex items-center gap-1 rounded bg-emerald-600 px-2 py-1 text-xs text-white hover:bg-emerald-700"
            >
              <ArrowUp size={12} />
              Restaurar
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
