import { useEffect, useState } from 'react';
import { apiJson, ApiError } from '../../../lib/api';
import type { OperateurResumen } from '../../../lib/api-types';

export default function Equipe() {
  const [items, setItems] = useState<OperateurResumen[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiJson<{ operateurs: OperateurResumen[]; total: number }>(
      '/tablero/api/v3/trabajo/equipe',
      { context: 'trabajo' }
    )
      .then((r) => setItems(r.operateurs))
      .catch((e: ApiError) => setError(e.code ?? e.message));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="di-title text-2xl">Équipe</h2>

      {error && (
        <div className="di-card p-3 text-sm">
          <span className="di-title text-[#D62828]">Erreur:</span> {error}
        </div>
      )}

      {items === null && !error && (
        <div className="text-sm text-neutral-700">Chargement…</div>
      )}

      {items?.map((op) => (
        <div key={op.id} className="di-card p-4">
          <div className="font-black uppercase tracking-tight">{op.id}</div>
          {op.nombre && (
            <div className="text-sm">{op.nombre}</div>
          )}
          {op.rol && (
            <div className="mt-2 di-chip">{op.rol}</div>
          )}
        </div>
      ))}
    </div>
  );
}
