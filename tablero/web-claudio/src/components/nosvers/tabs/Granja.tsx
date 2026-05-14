import { Sprout, Worm, Thermometer, CheckSquare, AlertTriangle, Phone } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type {
  HuertoSnapshot,
  VermiculturaSnapshot,
  ComposteurSnapshot,
  TareasDiaSnapshot,
  EiseniaRunSnapshot,
} from '../../../lib/api-types';

function WidgetHuertoActivo() {
  const { data } = useChannel<HuertoSnapshot>('huerto_estado');
  const cultivos = data?.cultivos ?? [];
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Sprout size={16} className="text-emerald-700" />
          Huerto activo
        </h3>
        <span className="text-xs text-muted">{cultivos.length} cultivos</span>
      </div>
      {cultivos.length === 0 ? (
        <EmptyState text="Sin cultivos registrados." />
      ) : (
        <div className="space-y-1.5">
          {cultivos.slice(0, 5).map((c) => (
            <div key={c.nombre} className="flex items-center justify-between py-1.5 border-b border-emerald-100 last:border-0">
              <div className="min-w-0 flex-1">
                <div className="text-sm text-fg truncate">{c.nombre}</div>
                <div className="text-xs text-muted">
                  {c.area_m2 ? `${c.area_m2} m²` : ''}
                  {c.cosecha_prev ? ` · cosecha ${c.cosecha_prev}` : ''}
                </div>
              </div>
              <span className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full ${
                c.estado === 'maduro' ? 'bg-amber-100 text-amber-800' :
                c.estado === 'creciendo' ? 'bg-emerald-100 text-emerald-800' :
                'bg-lime-100 text-lime-800'
              }`}>
                {c.estado}
              </span>
            </div>
          ))}
        </div>
      )}
      {data?.ultimo_riego_general && (
        <div className="mt-3 text-xs text-muted">
          Último riego: <span className="text-fg">{data.ultimo_riego_general}</span>
        </div>
      )}
    </Card>
  );
}

function WidgetVermicultura() {
  const { data } = useChannel<VermiculturaSnapshot>('vermicultura');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Worm size={16} className="text-emerald-700" />
          Vermicultura
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Worm size={16} className="text-emerald-700" />
        Vermicultura
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Eisenia biomasa" value={`${data.eisenia.biomasa_kg} kg`} accent="emerald" size="sm" />
        <Stat label="Bacs activos" value={data.eisenia.bacs} accent="emerald" size="sm" />
        <Stat label="Dendrobaena stock" value={`${data.dendrobaena.stock_g} g`} accent="lime" size="sm" />
        <Stat label="Reservadas" value={`${data.dendrobaena.reservadas_g} g`} accent="amber" size="sm" />
      </div>
      <div className="mt-3 p-2.5 rounded-lg bg-emerald-50/60 border border-emerald-100">
        <div className="text-xs text-muted">AAPPMA · pedido activo</div>
        <div className="text-sm text-fg mt-0.5">
          {data.aappma.pedido_activo.cliente} · {data.aappma.pedido_activo.cantidad_g} g
        </div>
        <div className="text-[11px] text-muted">
          Entrega {data.aappma.pedido_activo.fecha_entrega} · {data.aappma.pedido_activo.estado}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2 text-[11px] text-muted">
        <Phone size={11} />
        <span className="text-fg">{data.thierry.nombre}</span>
        <span>·</span>
        <span>{data.thierry.telefono}</span>
      </div>
    </Card>
  );
}

function WidgetComposteur() {
  const { data } = useChannel<ComposteurSnapshot>('composteur');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Thermometer size={16} className="text-emerald-700" />
        Composteur
      </h3>
      {!data ? (
        <EmptyState text="Cargando…" />
      ) : !data.activo ? (
        <div className="text-sm text-muted">{data.nota || 'No instalado todavía.'}</div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Temp." value={`${data.temperatura_c}°`} accent="amber" size="sm" />
            <Stat label="Humedad" value={`${data.humedad_pct}%`} accent="emerald" size="sm" />
            <Stat label="Fase" value={data.fase} accent="lime" size="sm" />
          </div>
          <div className="mt-2 text-[11px] text-muted">
            Última volteada: {data.ultima_volteada} · próxima: {data.proxima_volteada}
          </div>
        </>
      )}
    </Card>
  );
}

function WidgetTareasDia() {
  const { data } = useChannel<TareasDiaSnapshot>('tareas_dia');
  const tareas = data?.tareas ?? [];
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <CheckSquare size={16} className="text-emerald-700" />
          Tareas del día
        </h3>
        <span className="text-xs text-muted">
          {data?.hechas ?? 0}/{data?.total ?? 0} hechas
        </span>
      </div>
      {tareas.length === 0 ? (
        <EmptyState text="Sin tareas para hoy." />
      ) : (
        <div className="space-y-1.5">
          {tareas.slice(0, 6).map((t, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5 border-b border-emerald-100 last:border-0">
              <input type="checkbox" checked={t.hecha} readOnly
                className="mt-1 accent-emerald-600 flex-shrink-0" />
              <div className="min-w-0 flex-1">
                <div className={`text-sm ${t.hecha ? 'text-muted line-through' : 'text-fg'}`}>
                  {t.texto}
                </div>
                <div className="text-[11px] text-muted uppercase tracking-wide">
                  {t.categoria}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetEiseniaUltimaRun() {
  const { data } = useChannel<EiseniaRunSnapshot>('eisenia_run');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <AlertTriangle size={16} className="text-emerald-700" />
        Eisenia · última run
      </h3>
      {!data ? (
        <EmptyState text="Cargando…" />
      ) : (
        <>
          <div className="text-xs text-muted">
            {data.ultima_ejecucion ?? 'Sin ejecuciones'}
          </div>
          <div className="text-sm text-fg mt-1">{data.resumen}</div>
          {data.alertas.length > 0 && (
            <div className="mt-3 space-y-1.5">
              {data.alertas.slice(0, 4).map((a, i) => (
                <div key={i} className="flex items-center justify-between py-1 border-b border-emerald-100 last:border-0">
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-fg">{a.type.replace(/_/g, ' ')}</div>
                    <div className="text-[11px] text-muted">
                      {a.bac && `bac ${a.bac}`}
                      {typeof a.jours === 'number' && ` · ${a.jours} j`}
                      {typeof a.kg_estimes === 'number' && ` · ${a.kg_estimes} kg`}
                    </div>
                  </div>
                  <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full ${
                    a.urgence === 'urgente' || a.urgence === 'alta' || a.urgence === 'high'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-lime-100 text-lime-800'
                  }`}>
                    {a.urgence}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Card>
  );
}

export default function Granja() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg flex items-center gap-2">
        <Sprout size={22} className="text-emerald-700" />
        Granja
      </h2>
      <WidgetHuertoActivo />
      <WidgetVermicultura />
      <WidgetComposteur />
      <WidgetTareasDia />
      <WidgetEiseniaUltimaRun />
    </div>
  );
}
