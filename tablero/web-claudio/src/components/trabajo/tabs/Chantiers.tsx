import { useChannel } from '../../../lib/ws';
import type { ChantiersActivosSnapshot, ChantierWS } from '../../../lib/api-types';

const ESTADO_STYLE: Record<string, { label: string; cls: string }> = {
  urgente: { label: 'URGENT', cls: 'bg-[#D62828] text-white' },
  en_cours: { label: 'EN COURS', cls: 'bg-black text-white' },
  debut: { label: 'DÉBUT', cls: 'bg-white text-black border-2 border-black' },
  pausado: { label: 'PAUSE', cls: 'bg-neutral-300 text-black' },
};

function ChantierCard({ c }: { c: ChantierWS }) {
  const estado = ESTADO_STYLE[c.estado] ?? ESTADO_STYLE.en_cours;
  return (
    <div className="di-card p-4">
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className={`di-title text-[10px] px-2 py-1 ${estado.cls}`}>
          {estado.label}
        </span>
        <span className="bg-[#D62828] text-white di-title text-[10px] px-2 py-1 whitespace-nowrap">
          {c.devis_eur.toLocaleString('fr')} €
        </span>
      </div>
      <div className="font-black text-base uppercase tracking-tight leading-tight">
        {c.nombre}
      </div>
      <div className="text-[10px] text-neutral-700 uppercase mt-1 tracking-tight">
        {c.cliente}
      </div>
      {c.direccion && (
        <div className="text-[11px] mt-1 text-neutral-600">{c.direccion}</div>
      )}
      {(c.equipe_ids ?? []).length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {(c.equipe_ids ?? []).slice(0, 5).map((e) => (
            <span key={e} className="di-chip text-[9px] py-0.5 px-2">
              {e}
            </span>
          ))}
        </div>
      )}
      <div className="mt-3 flex items-center justify-between border-t-2 border-black pt-2">
        <span className="di-title text-[10px] text-neutral-600">
          {c.fecha_inicio} → {c.fecha_fin_prev || '—'}
        </span>
        {c.dias_restantes != null && (
          <span className={`di-title text-[10px] ${
            c.dias_restantes < 0 ? 'text-[#D62828]' :
            c.dias_restantes < 7 ? 'text-amber-700' :
            'text-neutral-700'
          }`}>
            {c.dias_restantes >= 0 ? `J-${c.dias_restantes}` : `RETARD ${-c.dias_restantes}j`}
          </span>
        )}
      </div>
    </div>
  );
}

export default function Chantiers() {
  const { data } = useChannel<ChantiersActivosSnapshot>('chantiers_activos');
  const items = data?.items ?? [];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="di-title text-2xl">CHANTIERS</h2>
        <span className="di-chip">{items.length}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">URGENT</div>
          <div className="font-black text-2xl text-[#D62828] leading-none mt-1">
            {data?.urgentes ?? 0}
          </div>
        </div>
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">EN COURS</div>
          <div className="font-black text-2xl leading-none mt-1">
            {data?.en_cours ?? 0}
          </div>
        </div>
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">DÉBUT</div>
          <div className="font-black text-2xl leading-none mt-1">
            {data?.debut ?? 0}
          </div>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="di-card p-4 text-sm">
          Aucun chantier actif.
        </div>
      ) : (
        items.map((c) => <ChantierCard key={c.slug} c={c} />)
      )}
    </div>
  );
}
