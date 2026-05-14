import { useChannel } from '../../../lib/ws';

interface ComprasSnap {
  items?: Array<{ texto: string; autor: string; urgente?: boolean }>;
  total?: number;
  empty?: boolean;
}

export default function ListasTab() {
  const { data } = useChannel<ComprasSnap>('compras');
  const items = data?.items ?? [];
  return (
    <div className="space-y-3">
      <h2 className="font-display text-xl mb-2">Lista de compras</h2>
      {items.length === 0 ? (
        <p className="text-muted text-sm">Lista vacía.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((it, i) => (
            <li
              key={i}
              className={`p-3 rounded-lg border border-border flex items-center justify-between ${
                it.urgente ? 'bg-amber-100' : 'bg-bg'
              }`}
            >
              <span>{it.texto}</span>
              <span className="text-xs text-muted">{it.autor}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
