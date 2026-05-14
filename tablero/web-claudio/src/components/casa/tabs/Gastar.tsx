import { useChannel } from '../../../lib/ws';

interface GastosSnap {
  mes?: string;
  total_mes_eur?: number;
  por_categoria?: Record<string, number>;
  n_apuntes?: number;
  empty?: boolean;
}

export default function GastarTab() {
  const { data } = useChannel<GastosSnap>('gastos');
  const total = data?.total_mes_eur ?? 0;
  const cats = Object.entries(data?.por_categoria ?? {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 6);
  return (
    <div className="space-y-4">
      <h2 className="font-display text-xl">Gastos del mes</h2>
      <div className="p-5 bg-bg border border-border rounded-2xl">
        <div className="text-xs text-muted">{data?.mes ?? ''}</div>
        <div className="font-display text-4xl text-primary mt-1">
          {total.toFixed(0)} €
        </div>
        <div className="text-xs text-muted mt-1">
          {data?.n_apuntes ?? 0} apuntes
        </div>
      </div>
      {cats.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {cats.map(([cat, eur]) => (
            <div key={cat} className="p-3 bg-bg border border-border rounded-lg">
              <div className="text-xs text-muted capitalize">{cat}</div>
              <div className="font-display text-lg">{eur.toFixed(0)} €</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
