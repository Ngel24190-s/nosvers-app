import { Phone, Mail, Worm, Package } from 'lucide-react';
import { useChannel } from '../../../lib/ws';
import { Card, Stat, EmptyState } from '../../widgets';
import type { AappmaStockSnapshot } from '../../../lib/api-types';

function WidgetContactosAAPPMA() {
  const { data } = useChannel<AappmaStockSnapshot>('aappma_stock');
  const contactos = data?.contactos ?? [];
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Phone size={16} className="text-emerald-700" />
        Contactos AAPPMA Neuvic
      </h3>
      {contactos.length === 0 ? (
        <EmptyState text="Sin contactos guardados." />
      ) : (
        <div className="space-y-2">
          {contactos.map((c) => (
            <div key={c.nombre} className="p-3 rounded-lg bg-emerald-50/40 border border-emerald-100">
              <div className="font-medium text-fg">{c.nombre}</div>
              <div className="text-xs text-muted">{c.rol}</div>
              <div className="flex gap-2 mt-2">
                {c.telefono && (
                  <a
                    href={`tel:${c.telefono.replace(/\s/g, '')}`}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-600 text-white text-xs active:scale-95 transition-transform"
                  >
                    <Phone size={12} />
                    {c.telefono}
                  </a>
                )}
                {c.email && (
                  <a
                    href={`mailto:${c.email}`}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-stone-100 text-stone-700 text-xs"
                  >
                    <Mail size={12} />
                    Email
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

function WidgetStockLombrices() {
  const { data } = useChannel<AappmaStockSnapshot>('aappma_stock');
  if (!data || data.empty) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Worm size={16} className="text-emerald-700" />
          Stock Dendrobaena
        </h3>
        <EmptyState text="Sin stock registrado." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Worm size={16} className="text-emerald-700" />
        Stock Dendrobaena
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <Stat
          label="Disponibles"
          value={`${data.dendrobaena_disponibles_g ?? 0} g`}
          accent="emerald"
          size="md"
        />
        <Stat
          label="Reservadas"
          value={`${data.dendrobaena_reservadas_g ?? 0} g`}
          accent="amber"
          size="md"
        />
      </div>
      {data.proxima_entrega && (
        <div className="mt-3 text-sm">
          <span className="text-muted">Próxima entrega: </span>
          <span className="text-fg font-medium">{data.proxima_entrega}</span>
        </div>
      )}
    </Card>
  );
}

function WidgetPedidoActivo() {
  const { data } = useChannel<AappmaStockSnapshot>('aappma_stock');
  const p = data?.pedido_activo;
  if (!p) {
    return (
      <Card className="p-4">
        <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
          <Package size={16} className="text-emerald-700" />
          Pedido activo
        </h3>
        <EmptyState text="Sin pedidos en curso." />
      </Card>
    );
  }
  return (
    <Card className="p-4">
      <h3 className="font-display text-base text-fg flex items-center gap-2 mb-3">
        <Package size={16} className="text-emerald-700" />
        Pedido activo
      </h3>
      <div className="space-y-2">
        <div className="font-display text-lg text-fg">{p.cliente}</div>
        <div className="grid grid-cols-2 gap-3">
          <Stat label="Cantidad" value={`${p.cantidad_g ?? 0} g`} accent="emerald" size="sm" />
          <Stat
            label="Entrega"
            value={p.fecha_entrega || '—'}
            sub={p.estado}
            accent="amber"
            size="sm"
          />
        </div>
      </div>
    </Card>
  );
}

export default function AAPPMA() {
  return (
    <div className="space-y-3">
      <h2 className="font-display text-2xl text-fg">AAPPMA Neuvic</h2>
      <WidgetPedidoActivo />
      <WidgetStockLombrices />
      <WidgetContactosAAPPMA />
    </div>
  );
}
