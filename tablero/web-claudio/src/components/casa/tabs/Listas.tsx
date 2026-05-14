import { useState } from 'react';
import { ShoppingCart, AlertTriangle, Plus } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, EmptyState } from '../../widgets';
import type { ComprasSnapshot } from '../../../lib/api-types';

function WidgetListaCompras() {
  const { data } = useChannel<ComprasSnapshot>('compras');
  const items = data?.items ?? [];
  const urgentes = items.filter((it) => it.urgente);
  const normales = items.filter((it) => !it.urgente);
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-base text-fg flex items-center gap-2">
          <ShoppingCart size={16} className="text-amber-700" />
          Por comprar
        </h3>
        <span className="text-xs text-muted">{items.length} ítems</span>
      </div>
      {items.length === 0 ? (
        <EmptyState text="Lista vacía." hint="Dicta «añade leche a la lista»" />
      ) : (
        <div className="space-y-1.5">
          {urgentes.map((it, i) => (
            <CheckboxRow
              key={`u-${i}`}
              texto={it.texto}
              autor={it.autor}
              urgente
            />
          ))}
          {normales.map((it, i) => (
            <CheckboxRow
              key={`n-${i}`}
              texto={it.texto}
              autor={it.autor}
            />
          ))}
        </div>
      )}
    </Card>
  );
}

function CheckboxRow({ texto, autor, urgente }: { texto: string; autor: string; urgente?: boolean }) {
  const [done, setDone] = useState(false);
  return (
    <button
      onClick={() => setDone((d) => !d)}
      className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-colors active:scale-[0.99] ${
        urgente
          ? 'bg-amber-50 border-amber-200'
          : 'bg-bg border-border'
      } ${done ? 'opacity-50' : ''}`}
    >
      <span
        className={`shrink-0 w-6 h-6 rounded-md border-2 flex items-center justify-center ${
          done
            ? 'bg-primary border-primary text-on-primary'
            : 'border-stone-300 bg-white'
        }`}
      >
        {done && '✓'}
      </span>
      <div className="flex-1 text-left min-w-0">
        <div className={`text-fg ${done ? 'line-through' : ''}`}>
          {urgente && (
            <AlertTriangle size={14} className="inline text-amber-700 mr-1 -mt-0.5" />
          )}
          {texto}
        </div>
        {autor && <div className="text-xs text-muted">{autor}</div>}
      </div>
    </button>
  );
}

function WidgetQuickAdd() {
  const [val, setVal] = useState('');
  const [enviando, setEnviando] = useState(false);
  const submit = async () => {
    if (!val.trim()) return;
    setEnviando(true);
    try {
      console.log('[lista] añadir', val);
      // TODO: endpoint persistencia compras (fuera de alcance 009)
      setVal('');
    } finally {
      setEnviando(false);
    }
  };
  return (
    <Card className="p-3">
      <div className="flex gap-2">
        <input
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Añadir a la lista…"
          className="flex-1 px-3 py-2.5 rounded-lg bg-white border border-stone-200 text-fg placeholder:text-muted focus:outline-none focus:border-primary"
        />
        <button
          onClick={submit}
          disabled={!val.trim() || enviando}
          className="shrink-0 w-11 h-11 rounded-lg bg-primary text-on-primary flex items-center justify-center disabled:opacity-40 active:scale-95 transition-transform"
        >
          <Plus size={20} />
        </button>
      </div>
    </Card>
  );
}

export default function ListasTab() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">Lista de compras</h2>
      <WidgetListaCompras />
      <WidgetQuickAdd />
    </div>
  );
}
