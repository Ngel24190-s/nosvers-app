import { Sun, Sunrise, Sunset, Moon, Bell, UtensilsCrossed, Pill, Dog, Wallet } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useChannel } from '../../../lib/ws';
import { getSub } from '../../../lib/auth';
import { Card, Stat, ListItem, EmptyState, Sparkbar } from '../../widgets';
import type {
  RecordatoriosSnapshot, MenuHoySnapshot, MedicacionSnapshot,
  BrisSnapshot, GastosSnapshot,
} from '../../../lib/api-types';

const PRESUPUESTO_MES = 1500;

function franjaSaludo(h: number): { label: string; Icon: typeof Sun } {
  if (h < 6) return { label: 'Buenas noches', Icon: Moon };
  if (h < 12) return { label: 'Buenos días', Icon: Sunrise };
  if (h < 19) return { label: 'Buenas tardes', Icon: Sun };
  return { label: 'Buenas noches', Icon: Sunset };
}

function WidgetSaludo() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);
  const { label, Icon } = franjaSaludo(now.getHours());
  const sub = getSub() || 'Angel';
  const hora = now.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  return (
    <Card className="p-5">
      <div className="flex items-center gap-3">
        <span className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-700">
          <Icon size={20} />
        </span>
        <div className="flex-1">
          <div className="text-xs text-muted uppercase tracking-wide">{hora}</div>
          <div className="font-display text-2xl text-fg leading-tight">
            {label}, {sub}
          </div>
        </div>
      </div>
    </Card>
  );
}

function WidgetRecordatoriosHoy() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  const hoy = new Date().toISOString().slice(0, 10);
  const items = (data?.items ?? [])
    .filter((it) => !it.hecho && it.fecha <= hoy)
    .sort((a, b) => b.prioridad - a.prioridad)
    .slice(0, 4);
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Bell size={16} className="text-amber-700" />
          Recordatorios hoy
        </h3>
        <span className="text-xs text-muted">{data?.total_hoy ?? items.length}</span>
      </div>
      {items.length === 0 ? (
        <EmptyState text="Día tranquilo." />
      ) : (
        <div className="space-y-2">
          {items.map((it) => (
            <ListItem
              key={it.slug}
              title={it.texto}
              meta={`${it.fecha} · ${it.autor || '—'}`}
              accent={it.prioridad >= 4 ? 'urgent' : 'neutral'}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetMenuHoy() {
  const { data } = useChannel<MenuHoySnapshot>('menu_dia');
  const hay = data && !data.empty && (data.comida || data.cena);
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <UtensilsCrossed size={16} className="text-amber-700" />
        Menú del día
      </h3>
      {!hay ? (
        <EmptyState text="Sin menú definido para hoy." hint="Dicta a Claudio: «menú: lasaña / ensalada»" />
      ) : (
        <div className="space-y-2 text-sm">
          {data?.comida && (
            <div className="flex gap-2">
              <span className="text-xs text-muted w-16 shrink-0 uppercase tracking-wide pt-0.5">Comida</span>
              <span className="text-fg flex-1">{data.comida}</span>
            </div>
          )}
          {data?.cena && (
            <div className="flex gap-2">
              <span className="text-xs text-muted w-16 shrink-0 uppercase tracking-wide pt-0.5">Cena</span>
              <span className="text-fg flex-1">{data.cena}</span>
            </div>
          )}
          {data?.postre && (
            <div className="flex gap-2">
              <span className="text-xs text-muted w-16 shrink-0 uppercase tracking-wide pt-0.5">Postre</span>
              <span className="text-fg flex-1">{data.postre}</span>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function WidgetMedicacionProxima() {
  const { data } = useChannel<MedicacionSnapshot>('medicacion');
  const prox = data?.proxima;
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Pill size={16} className="text-amber-700" />
        Próxima toma
      </h3>
      {!prox ? (
        <EmptyState text="Sin medicaciones programadas." />
      ) : (
        <div>
          <div className="font-display text-2xl text-fg">{prox.medicamento}</div>
          <div className="text-sm text-muted mt-1">
            {prox.quien} · {prox.hora}
            {prox.en_minutos >= 0 && (
              <span className="ml-2 text-amber-700">
                en {prox.en_minutos < 60 ? `${prox.en_minutos} min` : `${Math.round(prox.en_minutos / 60)} h`}
              </span>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

function WidgetBrisResumen() {
  const { data } = useChannel<BrisSnapshot>('bris');
  if (!data || data.empty) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Dog size={16} className="text-amber-700" />
          Bris
        </h3>
        <EmptyState text="Sin notas de Bris." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Dog size={16} className="text-amber-700" />
        Bris
      </h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        {data.ultimo_paseo && (
          <div>
            <div className="text-xs text-muted uppercase">Último paseo</div>
            <div className="text-fg mt-0.5">{data.ultimo_paseo}</div>
          </div>
        )}
        {data.proxima_vacuna && (
          <div>
            <div className="text-xs text-muted uppercase">Próx. vacuna</div>
            <div className="text-fg mt-0.5">{data.proxima_vacuna}</div>
          </div>
        )}
        {data.peso_kg !== undefined && data.peso_kg !== null && (
          <div>
            <div className="text-xs text-muted uppercase">Peso</div>
            <div className="text-fg mt-0.5">{data.peso_kg} kg</div>
          </div>
        )}
        {data.animo && (
          <div>
            <div className="text-xs text-muted uppercase">Ánimo</div>
            <div className="text-fg mt-0.5 capitalize">{data.animo}</div>
          </div>
        )}
      </div>
    </Card>
  );
}

function WidgetGastosMesMini() {
  const { data } = useChannel<GastosSnapshot>('gastos');
  const total = data?.total_mes_eur ?? 0;
  const presupuesto = data?.presupuesto_mes_eur ?? PRESUPUESTO_MES;
  const ratio = presupuesto > 0 ? total / presupuesto : 0;
  const accent = ratio < 0.6 ? 'emerald' : ratio < 0.9 ? 'amber' : 'danger';
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Wallet size={16} className="text-amber-700" />
        Gastos del mes
      </h3>
      <Stat
        label={data?.mes ?? ''}
        value={`${total.toFixed(0)} €`}
        sub={`de ${presupuesto.toFixed(0)} € · ${data?.n_apuntes ?? 0} apuntes`}
        accent="amber"
        size="md"
      />
      <div className="mt-3">
        <Sparkbar value={total} max={presupuesto} accent={accent} height={8} />
      </div>
    </Card>
  );
}

export default function HoyTab() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Hoy</h2>
      <WidgetSaludo />
      <WidgetRecordatoriosHoy />
      <WidgetMenuHoy />
      <WidgetMedicacionProxima />
      <WidgetBrisResumen />
      <WidgetGastosMesMini />
    </div>
  );
}
