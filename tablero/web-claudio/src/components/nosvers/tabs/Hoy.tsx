import { Sunrise, Globe, ShoppingBag, Bell, TrendingUp, Calendar } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type {
  BriefingAfricaSnapshot,
  PedidosStripeSnapshot,
  ProximaPublicacionSnapshot,
  RecordatoriosSnapshot,
  RevenueSnapshot,
} from '../../../lib/api-types';

function WidgetBriefingAfrica() {
  const { data } = useChannel<BriefingAfricaSnapshot>('briefing_africa');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-2">
        <Globe size={16} className="text-emerald-700" />
        Briefing África
      </h3>
      {!data ? (
        <EmptyState text="Cargando…" />
      ) : (
        <>
          <div className="text-xs text-muted">{data.fecha}</div>
          <div className="text-sm text-fg mt-1 font-medium">{data.titulo}</div>
          <p className="text-sm text-muted mt-2 leading-relaxed">
            {data.extracto || 'Sin extracto disponible.'}
          </p>
          {data.items?.length > 1 && (
            <div className="text-[11px] text-muted mt-2">
              {data.items.length} bloque(s) en el resultado
            </div>
          )}
        </>
      )}
    </Card>
  );
}

function WidgetPedidosHoy() {
  const { data } = useChannel<PedidosStripeSnapshot>('pedidos_stripe');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <ShoppingBag size={16} className="text-emerald-700" />
        Pedidos · hoy
      </h3>
      {!data || data.empty ? (
        <EmptyState text="Sin pedidos todavía." />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Pedidos mes" value={data.pedidos_mes ?? 0} accent="emerald" size="sm" />
            <Stat label="Total mes" value={`${(data.mes_total_eur ?? 0).toFixed(0)} €`} accent="emerald" size="sm" />
          </div>
          {data.ultimo && (
            <div className="mt-3 p-2.5 rounded-lg bg-lime-50 border border-lime-200/60">
              <div className="text-xs text-muted">Último pedido</div>
              <div className="text-sm text-fg mt-0.5">
                {data.ultimo.producto} · {(data.ultimo.eur ?? 0).toFixed(2)} €
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
}

function WidgetProximaPublicacion() {
  const { data } = useChannel<ProximaPublicacionSnapshot>('proxima_publicacion');
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Calendar size={16} className="text-emerald-700" />
        Próxima publicación
      </h3>
      {!data || !data.siguiente ? (
        <EmptyState text="Sin posts en cola." />
      ) : (
        <>
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
              POST {data.siguiente.n}
            </span>
            <span className="text-muted">
              {data.siguiente.dia} · {data.siguiente.hora}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 ml-auto text-[10px]">
              {data.siguiente.status}
            </span>
          </div>
          {data.siguiente.tipo && (
            <div className="text-[11px] text-muted mt-1">{data.siguiente.tipo}</div>
          )}
          <p className="text-sm text-fg mt-2 leading-relaxed line-clamp-3">
            {data.siguiente.caption || '(sin caption todavía)'}
          </p>
          <div className="mt-3 text-[11px] text-muted">
            {data.pendientes} pendiente(s) · {data.aprobados} aprobado(s)
          </div>
        </>
      )}
    </Card>
  );
}

function WidgetRecordatoriosNosVers() {
  const { data } = useChannel<RecordatoriosSnapshot>('recordatorios');
  const items = (data?.items ?? []).filter(
    (it) => /nosvers|ferme|granja|huerto|aappma/i.test(it.texto + ' ' + it.autor)
  );
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Bell size={16} className="text-emerald-700" />
        Recordatorios · NosVers
      </h3>
      {items.length === 0 ? (
        <EmptyState text="Sin recordatorios NosVers." />
      ) : (
        <div className="space-y-1.5">
          {items.slice(0, 5).map((it, i) => (
            <div key={i} className="flex items-start gap-2 py-1.5 border-b border-emerald-100 last:border-0">
              <input type="checkbox" checked={it.hecho} readOnly
                className="mt-1 accent-emerald-600" />
              <div className="min-w-0 flex-1">
                <div className="text-sm text-fg truncate">{it.texto}</div>
                <div className="text-[11px] text-muted">{it.fecha} · {it.autor}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetVentasMes() {
  const { data: rev } = useChannel<RevenueSnapshot>('revenue');
  const { data: ped } = useChannel<PedidosStripeSnapshot>('pedidos_stripe');
  const mrr = ped?.club_subs?.mrr_eur ?? 0;
  const totalMes = rev?.mes_actual_eur ?? ped?.mes_total_eur ?? 0;
  const ant = rev?.mes_anterior_eur ?? 0;
  const delta = totalMes - ant;
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <TrendingUp size={16} className="text-emerald-700" />
          Ventas · mes
        </h3>
        <span className="text-xs text-muted">
          MRR Club: <span className="text-emerald-700 font-medium">{mrr.toFixed(0)} €</span>
        </span>
      </div>
      <Stat
        label=""
        value={`${totalMes.toFixed(0)} €`}
        sub={
          ant > 0 ? (
            <span className={delta >= 0 ? 'text-emerald-700' : 'text-red-700'}>
              {delta >= 0 ? '+' : ''}{delta.toFixed(0)} € vs mes anterior
            </span>
          ) : null
        }
        accent="emerald"
        size="lg"
      />
    </Card>
  );
}

export default function Hoy() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg flex items-center gap-2">
        <Sunrise size={22} className="text-emerald-700" />
        NosVers · hoy
      </h2>
      <WidgetBriefingAfrica />
      <WidgetVentasMes />
      <WidgetPedidosHoy />
      <WidgetProximaPublicacion />
      <WidgetRecordatoriosNosVers />
    </div>
  );
}
