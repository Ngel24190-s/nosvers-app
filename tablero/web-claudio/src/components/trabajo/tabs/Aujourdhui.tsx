import { useChannel } from '../../../lib/ws';
import type { TrabajoSnapshot } from '../../../lib/api-types';

const SERVICIOS = ['Désamiantage', 'Déplombage', 'Décontamination', 'Démolition'];

export default function Aujourdhui() {
  const { data } = useChannel<TrabajoSnapshot>('trabajo');
  const ultimo = data?.ultimo_evento;
  return (
    <div className="space-y-4">
      <h2 className="di-title text-2xl">Aujourd'hui</h2>

      <div className="di-card p-4">
        <div className="bg-black text-white di-title text-xs px-2 py-1 inline-block mb-3">
          Chantiers actifs
        </div>
        <div className="font-black text-6xl text-[#D62828] leading-none">
          {data?.chantiers_activos ?? 0}
        </div>
        <div className="text-[10px] di-title mt-2">
          Équipe disponible: {data?.equipe_disponible ?? 0} opérateur(s)
        </div>
      </div>

      <div className="di-card p-4">
        <div className="bg-[#D62828] text-white di-title text-xs px-2 py-1 inline-block mb-3">
          Dernier événement
        </div>
        {ultimo ? (
          <>
            <div className="font-black text-sm uppercase tracking-tight">
              {ultimo.chantier} · {ultimo.tipo}
            </div>
            <div className="text-[10px] uppercase tracking-tight text-neutral-600">
              {ultimo.fecha}
            </div>
            <div className="mt-2 text-sm">{ultimo.descripcion}</div>
          </>
        ) : (
          <div className="text-sm text-neutral-700">Aucun événement récent.</div>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {SERVICIOS.map((s) => (
          <span key={s} className="di-chip">{s}</span>
        ))}
      </div>
    </div>
  );
}
