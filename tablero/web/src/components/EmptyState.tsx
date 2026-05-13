import { Sprout } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-tinta/15 bg-white/60 px-6 py-12 text-center">
      <div className="mx-auto mb-3 text-verde">
        <Sprout size={28} className="mx-auto" />
      </div>
      <h3 className="font-display text-lg">Aún no hay notas en este rango</h3>
      <p className="mt-2 text-sm text-tinta/60">
        Captura la primera con la PWA <span className="font-medium">voz</span> y aparecerá aquí.
      </p>
    </div>
  );
}
