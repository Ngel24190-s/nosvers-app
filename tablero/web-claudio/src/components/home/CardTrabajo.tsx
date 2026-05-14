import { useChannel } from '../../lib/ws';
import type { TrabajoSnapshot } from '../../lib/api-types';

// Card bicromático rojo DI + blanco. Homenaje a la furgoneta de Angel.
export default function CardTrabajo({ onSelect }: { onSelect: () => void }) {
  const { data } = useChannel<TrabajoSnapshot>('trabajo');
  const activos = data?.chantiers_activos ?? 0;
  return (
    <button
      onClick={onSelect}
      className="grid grid-cols-2 overflow-hidden rounded-none text-left
                 border-2 border-black active:scale-[0.99] transition-transform"
      style={{ minHeight: 168 }}
    >
      <div className="bg-white p-6 flex flex-col justify-between text-black">
        <div>
          <div className="font-black text-7xl leading-none tracking-di">DI</div>
          <div className="mt-1 text-[10px] font-bold tracking-tight uppercase">
            DI Environnement
          </div>
        </div>
        <div className="text-[10px] font-black uppercase tracking-tight">
          Désamiantage · Déplombage
        </div>
      </div>
      <div className="bg-[#D62828] p-6 flex flex-col justify-between text-white">
        <div className="text-[10px] font-black uppercase tracking-tight">
          Cond. Travaux
        </div>
        <div>
          <div className="font-black text-5xl leading-none">{activos}</div>
          <div className="text-[11px] font-black uppercase tracking-tight mt-1">
            {activos === 1 ? 'chantier actif' : 'chantiers actifs'}
          </div>
        </div>
      </div>
    </button>
  );
}
