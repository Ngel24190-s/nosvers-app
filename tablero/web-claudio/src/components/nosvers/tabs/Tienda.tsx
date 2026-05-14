import { TrendingUp, Users, Package } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type { RevenueSnapshot, PedidosStripeSnapshot } from '../../../lib/api-types';

function WidgetVentasMes() {
  const { data: rev } = useChannel<RevenueSnapshot>('revenue');
  const mes = rev?.mes_actual_eur ?? 0;
  const ant = rev?.mes_anterior_eur ?? 0;
  const delta = mes - ant;
  return (
    <Card className="p-5">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <TrendingUp size={16} className="text-emerald-700" />
        Ventas · mes actual
      </h3>
      <Stat
        label=""
        value={`${mes.toFixed(2)} €`}
        sub={`${rev?.pedidos_mes ?? 0} pedidos`}
        accent="emerald"
        size="lg"
      />
      {ant > 0 && (
        <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-emerald-100">
          <div>
            <div className="text-xs text-muted uppercase">Mes anterior</div>
            <div className="font-display text-xl text-fg mt-0.5">{ant.toFixed(0)} €</div>
          </div>
          <div>
            <div className="text-xs text-muted uppercase">Variación</div>
            <div className={`font-display text-xl mt-0.5 ${delta >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
              {delta >= 0 ? '+' : ''}{delta.toFixed(0)} €
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function WidgetClubSolVivantSuscriptores() {
  const { data } = useChannel<PedidosStripeSnapshot>('pedidos_stripe');
  const club = data?.club_subs;
  if (!club) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Users size={16} className="text-emerald-700" />
          Club Sol Vivant
        </h3>
        <EmptyState text="Sin suscripciones aún." hint="Lanzamiento M1: 20 plazas" />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Users size={16} className="text-emerald-700" />
        Club Sol Vivant
      </h3>
      <div className="grid grid-cols-3 gap-3">
        <Stat label="Activos" value={club.activos} accent="emerald" size="sm" />
        <Stat label="Nuevos mes" value={`+${club.nuevos_mes}`} accent="amber" size="sm" />
        <Stat label="MRR" value={`${club.mrr_eur.toFixed(0)} €`} accent="emerald" size="sm" />
      </div>
    </Card>
  );
}

function WidgetUltimoPedido() {
  const { data } = useChannel<PedidosStripeSnapshot>('pedidos_stripe');
  const u = data?.ultimo;
  if (!u) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Package size={16} className="text-emerald-700" />
          Último pedido
        </h3>
        <EmptyState text="Sin pedidos recientes." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Package size={16} className="text-emerald-700" />
        Último pedido
      </h3>
      <div className="space-y-2">
        <div className="font-display text-lg text-fg">{u.cliente}</div>
        <div className="text-sm text-muted">{u.producto}</div>
        <div className="flex items-center justify-between pt-2 border-t border-emerald-100">
          <span className="text-xs text-muted">{u.fecha}</span>
          <span className="font-display text-xl text-emerald-700">{(u.eur ?? 0).toFixed(2)} €</span>
        </div>
      </div>
    </Card>
  );
}

export default function Tienda() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Tienda · Stripe</h2>
      <WidgetVentasMes />
      <WidgetClubSolVivantSuscriptores />
      <WidgetUltimoPedido />
    </div>
  );
}
