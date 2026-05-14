import { Sprout, Calendar, Recycle, Thermometer } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, EmptyState, ListItem, Sparkbar } from '../../widgets';
import type { HuertoSnapshot } from '../../../lib/api-types';

const CALENDARIO_SIEMBRA: Record<number, string[]> = {
  1: ['Ajos', 'Habas', 'Cebollas'],
  2: ['Lechugas', 'Rábanos', 'Espinacas'],
  3: ['Tomates (semillero)', 'Pimientos', 'Calabacines'],
  4: ['Tomates (trasplante)', 'Judías verdes', 'Maíz dulce'],
  5: ['Pepinos', 'Melones', 'Calabazas', 'Albahaca'],
  6: ['Zanahorias tardías', 'Acelgas', 'Coles'],
  7: ['Lechugas otoño', 'Espinacas', 'Endivias'],
  8: ['Coles de invierno', 'Rábanos', 'Puerros'],
  9: ['Ajos', 'Habas', 'Espinacas'],
  10: ['Lechugas', 'Ajos', 'Cebollas'],
  11: ['Habas', 'Guisantes', 'Ajos'],
  12: ['Ajos', 'Cebollas tempranas'],
};

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

function WidgetCultivosActivos() {
  const { data } = useChannel<HuertoSnapshot>('huerto_estado');
  const cultivos = data?.cultivos ?? [];
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Sprout size={16} className="text-emerald-700" />
          Cultivos activos
        </h3>
        <span className="text-xs text-muted">{cultivos.length}</span>
      </div>
      {cultivos.length === 0 ? (
        <EmptyState text="Sin cultivos." />
      ) : (
        <div className="space-y-2">
          {cultivos.map((c) => (
            <div key={c.nombre} className="p-3 rounded-lg bg-emerald-50/40 border border-emerald-100">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-fg">{c.nombre}</div>
                  <div className="text-xs text-muted mt-0.5">
                    {c.area_m2 ? `${c.area_m2} m² · ` : ''}
                    siembra {c.siembra || '—'}
                  </div>
                </div>
                <span className={`text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full shrink-0 ${
                  c.estado === 'maduro' ? 'bg-amber-100 text-amber-800' :
                  c.estado === 'creciendo' ? 'bg-emerald-100 text-emerald-800' :
                  c.estado === 'cosechado' ? 'bg-stone-100 text-stone-700' :
                  'bg-lime-100 text-lime-800'
                }`}>
                  {c.estado}
                </span>
              </div>
              {c.ultimo_riego && (
                <div className="text-xs text-muted mt-2">
                  Último riego: <span className="text-fg">{c.ultimo_riego}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetCalendarioSiembra() {
  const mes = new Date().getMonth() + 1;
  const items = CALENDARIO_SIEMBRA[mes] || [];
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Calendar size={16} className="text-emerald-700" />
        Toca sembrar en {MESES[mes - 1]}
      </h3>
      {items.length === 0 ? (
        <EmptyState text="Sin sugerencias." />
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {items.map((i) => (
            <span key={i} className="px-2.5 py-1 rounded-full bg-lime-100 text-lime-800 text-sm">
              {i}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetCompostStatus() {
  const { data } = useChannel<HuertoSnapshot>('huerto_estado');
  const c = data?.compost;
  if (!c) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Recycle size={16} className="text-emerald-700" />
          Compost
        </h3>
        <EmptyState text="Sin datos del compost." />
      </Card>
    );
  }
  const nivelPct = c.nivel === 'alto' ? 0.9 : c.nivel === 'medio' ? 0.55 : 0.25;
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Recycle size={16} className="text-emerald-700" />
        Compost
      </h3>
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted">Nivel</span>
            <span className="font-medium text-fg capitalize">{c.nivel}</span>
          </div>
          <div className="mt-1.5">
            <Sparkbar value={nivelPct} max={1} accent="emerald" height={8} />
          </div>
        </div>
        {c.temperatura_c != null && (
          <ListItem
            Icon={Thermometer}
            title={`${c.temperatura_c} °C`}
            meta="temperatura interior"
          />
        )}
        {c.ultima_volteada && (
          <div className="text-xs text-muted">
            Última volteada: <span className="text-fg">{c.ultima_volteada}</span>
          </div>
        )}
      </div>
    </Card>
  );
}

export default function Huerto() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Huerto</h2>
      <WidgetCalendarioSiembra />
      <WidgetCultivosActivos />
      <WidgetCompostStatus />
    </div>
  );
}
