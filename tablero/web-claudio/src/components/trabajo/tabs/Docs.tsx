import { useState } from 'react';
import { useChannel } from '../../../lib/ws';
import type { DocumentosTrabajoSnapshot, DocItem } from '../../../lib/api-types';

const TIPOS_LABEL: Record<string, string> = {
  ppsps: 'PPSPS',
  plan_retrait: 'PLAN RETRAIT',
  devis: 'DEVIS',
  certificat: 'CERTIFICATS',
  diag_amiante: 'DIAG AMIANTE',
  autre: 'AUTRES',
};

const TIPOS_ORDEN = ['ppsps', 'plan_retrait', 'devis', 'certificat', 'diag_amiante', 'autre'];

function DocRow({ d }: { d: DocItem }) {
  return (
    <div className="border-t-2 border-black/10 py-2.5 first:border-0 first:pt-0">
      <div className="font-bold text-sm leading-tight">{d.nombre}</div>
      <div className="flex items-center gap-2 mt-1 text-[10px] di-title text-neutral-600">
        {d.chantier && d.chantier !== '—' && (
          <span>{d.chantier}</span>
        )}
        {d.size_kb != null && <span>· {d.size_kb.toFixed(1)} KB</span>}
        {d.fecha && <span>· {d.fecha}</span>}
      </div>
    </div>
  );
}

export default function Docs() {
  const { data } = useChannel<DocumentosTrabajoSnapshot>('documentos_trabajo');
  const por_tipo = data?.por_tipo ?? {};
  const tiposPresentes = TIPOS_ORDEN.filter((t) => (por_tipo[t]?.length ?? 0) > 0);
  const [tipoActivo, setTipoActivo] = useState<string>('todos');

  const visibles = tipoActivo === 'todos'
    ? tiposPresentes.flatMap((t) => por_tipo[t] ?? [])
    : por_tipo[tipoActivo] ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="di-title text-2xl">DOCUMENTS</h2>
        <span className="di-chip">{data?.total ?? 0}</span>
      </div>

      <div className="flex flex-wrap gap-1.5">
        <button
          onClick={() => setTipoActivo('todos')}
          className={`di-chip ${tipoActivo === 'todos' ? 'bg-[#D62828] border-[#D62828]' : ''}`}
        >
          TOUS
        </button>
        {tiposPresentes.map((t) => (
          <button
            key={t}
            onClick={() => setTipoActivo(t)}
            className={`di-chip ${tipoActivo === t ? 'bg-[#D62828] border-[#D62828]' : ''}`}
          >
            {TIPOS_LABEL[t]} · {por_tipo[t]?.length}
          </button>
        ))}
      </div>

      {visibles.length === 0 ? (
        <div className="di-card p-4 text-sm">Aucun document.</div>
      ) : tipoActivo === 'todos' ? (
        <div className="space-y-3">
          {tiposPresentes.map((t) => (
            <div key={t} className="di-card p-4">
              <div className="bg-black text-white di-title text-xs px-2 py-1 inline-block mb-2">
                {TIPOS_LABEL[t]} · {por_tipo[t]?.length}
              </div>
              <div>
                {(por_tipo[t] ?? []).slice(0, 4).map((d, i) => (
                  <DocRow key={`${t}-${i}`} d={d} />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="di-card p-4">
          {visibles.map((d, i) => (
            <DocRow key={i} d={d} />
          ))}
        </div>
      )}
    </div>
  );
}
