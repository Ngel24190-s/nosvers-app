import { useEffect, useState } from 'react';
import { apiJson, ApiError } from '../../../lib/api';
import type { ChantierResumen } from '../../../lib/api-types';

export default function Chantiers() {
  const [items, setItems] = useState<ChantierResumen[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiJson<{ chantiers: ChantierResumen[]; total: number }>(
      '/tablero/api/v3/trabajo/chantiers?estado=activos',
      { context: 'trabajo' }
    )
      .then((r) => setItems(r.chantiers))
      .catch((e: ApiError) => setError(e.code ?? e.message));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="di-title text-2xl">Chantiers actifs</h2>
        <span className="di-chip">{items?.length ?? 0}</span>
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
          Aucun chantier actif. Crée-en un par dictée: « Crée un chantier
          Bordeaux Nord pour Mairie de Bordeaux, devis 84500 euros ».
        </div>
      )}

      {items?.map((c) => (
        <div key={c.slug} className="di-card p-4">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="font-black text-base uppercase tracking-tight leading-tight">
                {c.nombre}
              </div>
              <div className="text-[10px] text-neutral-600 uppercase mt-1 tracking-tight">
                {c.cliente}
              </div>
            </div>
            <div className="bg-[#D62828] text-white di-title text-[10px] px-2 py-1 whitespace-nowrap">
              {c.devis_eur.toLocaleString('fr')} €
            </div>
          </div>
          {c.direccion && (
            <div className="text-[11px] mt-2 text-neutral-700">{c.direccion}</div>
          )}
          <div className="mt-3 flex flex-wrap gap-1">
            {c.equipe_ids.slice(0, 5).map((e) => (
              <span key={e} className="di-chip text-[9px] py-0.5 px-2">
                {e}
              </span>
            ))}
          </div>
          <div className="mt-3 text-[10px] di-title text-neutral-600">
            {c.fecha_inicio} → {c.fecha_fin_prev || '—'}
          </div>
        </div>
      ))}
    </div>
  );
}
