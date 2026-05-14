import { Car, Repeat, FileText, LogOut, User } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { clearToken, getSub } from '../../../lib/auth';
import { Card, Stat, ListItem, EmptyState } from '../../widgets';
import type { CocheSnapshot } from '../../../lib/api-types';

const RECURRENTES_MOCK = [
  { nombre: 'Internet Orange', dia: 5, eur: 39.99 },
  { nombre: 'Mutuelle MGEN', dia: 8, eur: 76.40 },
  { nombre: 'Assurance Maif (auto)', dia: 15, eur: 58.20 },
  { nombre: 'EDF Bleu Ciel', dia: 18, eur: 92.50 },
];

const DOCUMENTOS_MOCK = [
  { nombre: 'Bail logement Neuvic', tipo: 'Vivienda', fecha: '2025-09-12' },
  { nombre: 'Carte grise C3', tipo: 'Vehículo', fecha: '2024-06-03' },
  { nombre: 'Bulletins paie 2026 Q1', tipo: 'Trabajo', fecha: '2026-04-30' },
];

function WidgetCocheEstado() {
  const { data } = useChannel<CocheSnapshot>('coche');
  if (!data || data.empty) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Car size={16} className="text-amber-700" />
          Coche
        </h3>
        <EmptyState text="Sin datos del coche." hint="Edita knowledge_base/coche/INDEX.md" />
      </Card>
    );
  }
  const itvDias = data.itv_dias_falta;
  const itvAlerta = itvDias !== null && itvDias !== undefined && itvDias < 30;
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Car size={16} className="text-amber-700" />
        Coche · {data.modelo || '—'}
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <Stat
          label="ITV próxima"
          value={data.itv_proxima || '—'}
          sub={
            itvDias !== null && itvDias !== undefined
              ? <span className={itvAlerta ? 'text-red-700' : 'text-emerald-700'}>
                  {itvDias >= 0 ? `en ${itvDias} d` : `vencida ${-itvDias} d`}
                </span>
              : undefined
          }
          accent={itvAlerta ? 'amber' : 'neutral'}
          size="sm"
        />
        <Stat
          label="Kilómetros"
          value={data.kilometros != null ? data.kilometros.toLocaleString('es') : '—'}
          accent="neutral"
          size="sm"
        />
        <Stat
          label="Seguro"
          value={data.seguro_renovacion || '—'}
          sub={
            data.seguro_dias_falta != null
              ? `en ${data.seguro_dias_falta} d`
              : undefined
          }
          accent="neutral"
          size="sm"
        />
        <Stat
          label="Último mant."
          value={data.ultimo_mantenimiento || '—'}
          accent="neutral"
          size="sm"
        />
      </div>
      {data.matricula && (
        <div className="mt-3 inline-block px-2 py-1 rounded bg-stone-100 text-xs font-mono text-stone-700">
          {data.matricula}
        </div>
      )}
    </Card>
  );
}

function WidgetRecurrentesMes() {
  const dia = new Date().getDate();
  const proximos = RECURRENTES_MOCK
    .map((r) => ({ ...r, dias: r.dia >= dia ? r.dia - dia : r.dia + 30 - dia }))
    .sort((a, b) => a.dias - b.dias)
    .slice(0, 4);
  const totalMes = RECURRENTES_MOCK.reduce((s, r) => s + r.eur, 0);
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Repeat size={16} className="text-amber-700" />
          Cargos recurrentes
        </h3>
        <span className="text-xs text-muted">{totalMes.toFixed(0)} €/mes</span>
      </div>
      <div className="space-y-1.5">
        {proximos.map((r) => (
          <ListItem
            key={r.nombre}
            title={r.nombre}
            meta={`día ${r.dia} · en ${r.dias} d`}
          />
        ))}
      </div>
    </Card>
  );
}

function WidgetDocumentosRecientes() {
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <FileText size={16} className="text-amber-700" />
        Documentos
      </h3>
      <div className="space-y-1.5">
        {DOCUMENTOS_MOCK.map((d) => (
          <ListItem
            key={d.nombre}
            Icon={FileText}
            title={d.nombre}
            meta={`${d.tipo} · ${d.fecha}`}
            chevron
          />
        ))}
      </div>
    </Card>
  );
}

function WidgetSesion() {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3 mb-3">
        <span className="w-10 h-10 rounded-full bg-stone-100 flex items-center justify-center text-stone-700">
          <User size={20} />
        </span>
        <div>
          <div className="text-xs text-muted uppercase tracking-wide">Sesión</div>
          <div className="text-fg font-medium">{getSub()}</div>
        </div>
      </div>
      <button
        onClick={() => {
          clearToken();
          location.reload();
        }}
        className="w-full py-2.5 rounded-lg bg-stone-100 hover:bg-stone-200 text-fg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
      >
        <LogOut size={16} />
        Cerrar sesión
      </button>
    </Card>
  );
}

export default function CasaTab() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Casa</h2>
      <WidgetCocheEstado />
      <WidgetRecurrentesMes />
      <WidgetDocumentosRecientes />
      <WidgetSesion />
    </div>
  );
}
