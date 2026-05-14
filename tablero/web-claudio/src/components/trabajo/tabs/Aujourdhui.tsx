import { useChannel } from '../../../lib/ws';
import type {
  ChantiersActivosSnapshot, ChantiersAgendaSnapshot,
} from '../../../lib/api-types';

const SERVICIOS = ['DÉSAMIANTAGE', 'DÉPLOMBAGE', 'DÉCONTAMINATION', 'DÉMOLITION'];

function WidgetChantierUrgente() {
  const { data } = useChannel<ChantiersActivosSnapshot>('chantiers_activos');
  const urgente = (data?.items ?? []).find((c) => c.estado === 'urgente');
  return (
    <div className="di-card p-4">
      <div className="bg-[#D62828] text-white di-title text-xs px-2 py-1 inline-block mb-3">
        Chantier urgent
      </div>
      {!urgente ? (
        <div className="text-sm text-neutral-700 di-title">Aucun chantier urgent</div>
      ) : (
        <>
          <div className="font-black text-base uppercase tracking-tight leading-tight">
            {urgente.nombre}
          </div>
          <div className="text-[10px] uppercase tracking-tight text-neutral-700 mt-1">
            {urgente.cliente}
          </div>
          {urgente.direccion && (
            <div className="text-[11px] text-neutral-600 mt-1">{urgente.direccion}</div>
          )}
          <div className="mt-3 flex items-center gap-2">
            <span className="bg-black text-white di-title text-[10px] px-2 py-1">
              {urgente.devis_eur.toLocaleString('fr')} €
            </span>
            {urgente.dias_restantes != null && (
              <span className="bg-[#D62828] text-white di-title text-[10px] px-2 py-1">
                {urgente.dias_restantes >= 0 ? `J-${urgente.dias_restantes}` : `RETARD ${-urgente.dias_restantes}j`}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function WidgetAgendaHoy() {
  const { data } = useChannel<ChantiersAgendaSnapshot>('chantiers_agenda');
  const eventos = data?.eventos ?? [];
  return (
    <div className="di-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="bg-black text-white di-title text-xs px-2 py-1 inline-block">
          Agenda du jour
        </div>
        <span className="di-title text-[10px] text-neutral-600">
          {eventos.length} EVENTS
        </span>
      </div>
      {eventos.length === 0 ? (
        <div className="text-sm text-neutral-700">Aucun événement aujourd'hui.</div>
      ) : (
        <div className="space-y-2">
          {eventos.map((e, i) => (
            <div key={i} className="flex gap-3 items-start border-l-4 border-[#D62828] pl-3">
              <div className="bg-[#D62828] text-white di-title text-[10px] px-2 py-1 shrink-0">
                {e.hora}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-black text-xs uppercase tracking-tight">
                  {e.chantier}
                </div>
                <div className="text-xs text-neutral-700 mt-0.5">
                  <span className="di-title text-[10px] mr-1">{e.tipo}</span>
                  {e.descripcion}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WidgetEstadisticasRapidas() {
  const { data } = useChannel<ChantiersActivosSnapshot>('chantiers_activos');
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="di-card p-4">
        <div className="di-title text-[10px] text-neutral-600">Chantiers actifs</div>
        <div className="font-black text-5xl text-[#D62828] leading-none mt-1">
          {data?.total ?? 0}
        </div>
        <div className="di-title text-[9px] mt-2 text-neutral-600">
          {data?.urgentes ?? 0} URGENTS · {data?.en_cours ?? 0} EN COURS · {data?.debut ?? 0} DÉBUT
        </div>
      </div>
      <div className="di-card p-4 bg-black text-white">
        <div className="di-title text-[10px] text-neutral-300">Équipe</div>
        <div className="font-black text-5xl leading-none mt-1">
          {/* placeholder; equipe vendrá del canal equipe */}
          <span className="text-white">—</span>
        </div>
        <div className="di-title text-[9px] mt-2 text-neutral-300">
          OPÉRATEURS · VOIR ONGLET ÉQUIPE
        </div>
      </div>
    </div>
  );
}

function WidgetChipsServicios() {
  return (
    <div className="di-card p-3">
      <div className="di-title text-[10px] text-neutral-600 mb-2">Services DI</div>
      <div className="flex flex-wrap gap-1.5">
        {SERVICIOS.map((s) => (
          <span key={s} className="di-chip">{s}</span>
        ))}
      </div>
    </div>
  );
}

export default function Aujourdhui() {
  return (
    <div className="space-y-3">
      <h2 className="di-title text-2xl">AUJOURD'HUI</h2>
      <WidgetChantierUrgente />
      <WidgetEstadisticasRapidas />
      <WidgetAgendaHoy />
      <WidgetChipsServicios />
    </div>
  );
}
