import { useChannel } from '../../../lib/ws';
import type { EquipeSnapshot, OperateurWS } from '../../../lib/api-types';

const ESTADO_BADGE: Record<string, { label: string; cls: string }> = {
  actif: { label: 'ACTIF', cls: 'bg-[#D62828] text-white' },
  formation: { label: 'FORM.', cls: 'bg-black text-white' },
  absent: { label: 'ABSENT', cls: 'bg-neutral-300 text-black' },
  conge: { label: 'CONGÉ', cls: 'bg-neutral-200 text-black' },
};

function OperateurCard({ op }: { op: OperateurWS }) {
  const badge = ESTADO_BADGE[op.estado] ?? ESTADO_BADGE.actif;
  return (
    <div className="di-card p-3 flex items-center gap-3">
      <div className="w-12 h-12 bg-black text-white flex items-center justify-center font-black text-base tracking-tight shrink-0">
        {op.iniciales || '?'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="font-black uppercase tracking-tight leading-tight">
          {op.id}
        </div>
        <div className="text-xs text-neutral-700 truncate">{op.nombre}</div>
        {op.rol && (
          <div className="text-[10px] di-title text-neutral-600 truncate mt-0.5">
            {op.rol}
          </div>
        )}
      </div>
      <div className="shrink-0 flex flex-col items-end gap-1">
        <span className={`di-title text-[9px] px-2 py-0.5 ${badge.cls}`}>
          {badge.label}
        </span>
        {op.chantier_actual && op.chantier_actual !== '—' && (
          <span className="text-[9px] di-title text-neutral-600 text-right max-w-[110px] truncate">
            {op.chantier_actual}
          </span>
        )}
      </div>
    </div>
  );
}

export default function Equipe() {
  const { data } = useChannel<EquipeSnapshot>('equipe');
  const ops = data?.operateurs ?? [];
  return (
    <div className="space-y-4">
      <h2 className="di-title text-2xl">ÉQUIPE</h2>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">TOTAL</div>
          <div className="font-black text-2xl leading-none mt-1">
            {data?.total ?? 0}
          </div>
        </div>
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">ACTIFS</div>
          <div className="font-black text-2xl text-[#D62828] leading-none mt-1">
            {data?.actifs ?? 0}
          </div>
        </div>
        <div className="di-card p-2">
          <div className="di-title text-[9px] text-neutral-600">FORMATION</div>
          <div className="font-black text-2xl leading-none mt-1">
            {data?.en_formation ?? 0}
          </div>
        </div>
      </div>

      {ops.length === 0 ? (
        <div className="di-card p-4 text-sm">Aucun opérateur.</div>
      ) : (
        <div className="space-y-2">
          {ops.map((op) => <OperateurCard key={op.id} op={op} />)}
        </div>
      )}
    </div>
  );
}
