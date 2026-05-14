import { Sprout, ShoppingBag, Fish, Cloud, TrendingUp } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type {
  RevenueSnapshot, HuertoSnapshot, PedidosStripeSnapshot,
  AappmaStockSnapshot, ClimaSnapshot,
} from '../../../lib/api-types';

function WidgetIngresosMes() {
  const { data } = useChannel<RevenueSnapshot>('revenue');
  const mes = data?.mes_actual_eur ?? 0;
  const ant = data?.mes_anterior_eur ?? 0;
  const delta = mes - ant;
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <TrendingUp size={16} className="text-emerald-700" />
          Ingresos · mes actual
        </h3>
        <span className="text-xs text-muted">{data?.pedidos_mes ?? 0} pedidos</span>
      </div>
      <Stat
        label=""
        value={`${mes.toFixed(0)} €`}
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

function WidgetHuertoEstado() {
  const { data } = useChannel<HuertoSnapshot>('huerto_estado');
  const cultivos = data?.cultivos ?? [];
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Sprout size={16} className="text-emerald-700" />
          Huerto
        </h3>
        <span className="text-xs text-muted">{cultivos.length} cultivos</span>
      </div>
      {cultivos.length === 0 ? (
        <EmptyState text="Sin cultivos registrados." />
      ) : (
        <div className="space-y-1.5">
          {cultivos.slice(0, 3).map((c) => (
            <div key={c.nombre} className="flex items-center justify-between py-1.5 border-b border-emerald-100 last:border-0">
              <div className="min-w-0 flex-1">
                <div className="text-fg text-sm truncate">{c.nombre}</div>
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
          Último riego general: <span className="text-fg">{data.ultimo_riego_general}</span>
        </div>
      )}
    </Card>
  );
}

function WidgetPedidosStripe() {
  const { data } = useChannel<PedidosStripeSnapshot>('pedidos_stripe');
  if (!data || data.empty) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <ShoppingBag size={16} className="text-emerald-700" />
          Pedidos hoy
        </h3>
        <EmptyState text="Sin pedidos todavía." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <ShoppingBag size={16} className="text-emerald-700" />
        Tienda Stripe
      </h3>
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
    </Card>
  );
}

function WidgetAAPPMAStatus() {
  const { data } = useChannel<AappmaStockSnapshot>('aappma_stock');
  if (!data || data.empty) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Fish size={16} className="text-emerald-700" />
          AAPPMA Neuvic
        </h3>
        <EmptyState text="Sin stock registrado." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Fish size={16} className="text-emerald-700" />
        Dendrobaena · stock
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <Stat
          label="Disponibles"
          value={`${data.dendrobaena_disponibles_g ?? 0} g`}
          accent="emerald"
          size="sm"
        />
        <Stat
          label="Reservadas"
          value={`${data.dendrobaena_reservadas_g ?? 0} g`}
          accent="amber"
          size="sm"
        />
      </div>
      {data.proxima_entrega && (
        <div className="mt-2 text-xs text-muted">
          Próxima entrega: <span className="text-fg">{data.proxima_entrega}</span>
        </div>
      )}
    </Card>
  );
}

function WidgetClimaNeuvic() {
  const { data } = useChannel<ClimaSnapshot>('clima_neuvic');
  if (!data) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Cloud size={16} className="text-emerald-700" />
          Clima Neuvic
        </h3>
        <EmptyState text="Cargando…" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <Cloud size={16} className="text-emerald-700" />
          {data.ciudad ?? 'Neuvic'}
        </h3>
        <span className="text-xs text-muted">{data.weather_label}</span>
      </div>
      <div className="mt-2 flex items-baseline gap-3">
        <div className="font-display text-4xl text-emerald-700">
          {Math.round(data.temperatura_c ?? 0)}°
        </div>
        <div className="text-sm text-muted">
          ressentie {Math.round(data.sensacion_c ?? 0)}° ·
          vent {Math.round(data.viento_kmh ?? 0)} km/h
        </div>
      </div>
      {data.pronostico && data.pronostico.length > 0 && (
        <div className="grid grid-cols-3 gap-2 mt-3">
          {data.pronostico.slice(0, 3).map((p) => (
            <div key={p.fecha} className="text-center p-2 rounded-lg bg-emerald-50/50 border border-emerald-100">
              <div className="text-[10px] text-muted uppercase">{p.fecha.slice(5)}</div>
              <div className="text-sm font-medium text-fg mt-0.5">
                {Math.round(p.min)}° / {Math.round(p.max)}°
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

export default function HoyGranja() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Granja · hoy</h2>
      <WidgetIngresosMes />
      <WidgetClimaNeuvic />
      <WidgetHuertoEstado />
      <WidgetPedidosStripe />
      <WidgetAAPPMAStatus />
    </div>
  );
}
