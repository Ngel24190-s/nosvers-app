import { useEffect, useState } from 'react';
import { apiJson, ApiError } from '../../../lib/api';
import type { DocumentoResumen } from '../../../lib/api-types';

const FILTROS = ['todos', 'ppsps', 'devis', 'certificats', 'plans-retrait', 'diag-amiante'];

export default function Docs() {
  const [filtro, setFiltro] = useState('todos');
  const [items, setItems] = useState<DocumentoResumen[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setItems(null);
    setError(null);
    apiJson<{ documents: DocumentoResumen[]; total: number }>(
      `/tablero/api/v3/trabajo/documents?tipo=${encodeURIComponent(filtro)}`,
      { context: 'trabajo' }
    )
      .then((r) => setItems(r.documents))
      .catch((e: ApiError) => setError(e.code ?? e.message));
  }, [filtro]);

  return (
    <div className="space-y-4">
      <h2 className="di-title text-2xl">Documents</h2>

      <div className="flex flex-wrap gap-2">
        {FILTROS.map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`di-chip ${
              filtro === f ? 'bg-[#D62828] border-[#D62828]' : ''
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {error && (
        <div className="di-card p-3 text-sm">
          <span className="di-title text-[#D62828]">Erreur:</span> {error}
        </div>
      )}

      {items === null && !error && (
        <div className="text-sm text-neutral-700">Chargement…</div>
      )}

      {items && items.length === 0 && !error && (
        <div className="di-card p-4 text-sm">
          Aucun document {filtro !== 'todos' ? `de type ${filtro}` : ''}.
        </div>
      )}

      <div className="grid grid-cols-1 gap-3">
        {items?.map((d) => (
          <div key={`${d.tipo}-${d.nombre}`} className="di-card p-3">
            <div className="font-black uppercase tracking-tight text-xs">
              {d.tipo}
            </div>
            <div className="text-sm mt-1">{d.nombre}</div>
            <div className="text-[10px] text-neutral-600 mt-1">
              {(d.size / 1024).toFixed(1)} KB
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
