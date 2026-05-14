import { Receipt, PieChart, Star } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type { GastosSnapshot } from '../../../lib/api-types';

function WidgetTotalMes() {
  const { data } = useChannel<GastosSnapshot>('gastos');
  const mes = data?.total_mes_eur ?? 0;
  const ant = data?.total_mes_anterior_eur ?? 0;
  const delta = mes - ant;
  return (
    <Card className="p-5">
      <Stat
        label={data?.mes ?? 'Mes actual'}
        value={`${mes.toFixed(0)} €`}
        sub={`${data?.n_apuntes ?? 0} apuntes este mes`}
        accent="amber"
        size="lg"
      />
      {ant > 0 && (
        <div className={`text-sm mt-2 ${delta >= 0 ? 'text-red-700' : 'text-emerald-700'}`}>
          {delta >= 0 ? '+' : ''}{delta.toFixed(0)} € vs mes anterior
        </div>
      )}
    </Card>
  );
}

function WidgetUltimosGastos() {
  const { data } = useChannel<GastosSnapshot>('gastos');
  const ultimos = data?.ultimos ?? [];
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Receipt size={16} className="text-amber-700" />
        Últimos gastos
      </h3>
      {ultimos.length === 0 ? (
        <EmptyState text="Sin apuntes aún." />
      ) : (
        <div className="space-y-1">
          {ultimos.slice(0, 5).map((g, i) => (
            <div key={i} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
              <div className="min-w-0 flex-1">
                <div className="text-fg text-sm truncate">{g.concepto}</div>
                <div className="text-xs text-muted">
                  {g.fecha} · {g.categoria}
                </div>
              </div>
              <div className="font-display text-base text-fg shrink-0 ml-3">
                {g.eur.toFixed(2)} €
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetCategoriaMasUsada() {
  const { data } = useChannel<GastosSnapshot>('gastos');
  const cats = Object.entries(data?.por_categoria ?? {}).sort(([, a], [, b]) => b - a);
  const top = cats[0];
  if (!top) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Star size={16} className="text-amber-700" />
          Categoría top
        </h3>
        <EmptyState text="Sin datos por categoría." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Star size={16} className="text-amber-700" />
        Categoría top
      </h3>
      <div className="flex items-center justify-between">
        <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-amber-100 text-amber-800 font-medium capitalize">
          {top[0]}
        </span>
        <div className="font-display text-2xl text-fg">{top[1].toFixed(0)} €</div>
      </div>
    </Card>
  );
}

function WidgetPorCategoria() {
  const { data } = useChannel<GastosSnapshot>('gastos');
  const cats = Object.entries(data?.por_categoria ?? {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6);
  if (cats.length === 0) return null;
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <PieChart size={16} className="text-amber-700" />
        Por categoría
      </h3>
      <div className="grid grid-cols-2 gap-2">
        {cats.map(([cat, eur]) => (
          <div key={cat} className="p-3 bg-bg border border-border rounded-lg">
            <div className="text-xs text-muted capitalize">{cat}</div>
            <div className="font-display text-lg text-fg">{eur.toFixed(0)} €</div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function GastarTab() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Gastos</h2>
      <WidgetTotalMes />
      <WidgetCategoriaMasUsada />
      <WidgetUltimosGastos />
      <WidgetPorCategoria />
    </div>
  );
}
