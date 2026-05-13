import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Plus, Play, History, Pencil, Trash2 } from 'lucide-react';
import { apiAutomations, type AutomationSummary, type Catalog, type Automation } from './lib/apiAutomations';
import { AutomationEditor } from './AutomationEditor';
import { ExecutionHistoryModal } from './ExecutionHistoryModal';
import { toast, Toaster } from 'sonner';

interface Props {
  onBack: () => void;
}

const STATUS_DOT: Record<string, string> = {
  ok: 'bg-accent-green',
  partial: 'bg-accent-orange',
  error: 'bg-accent-orange',
  interrupted: 'bg-cockpit-textDim',
};

export function AutomationListPage({ onBack }: Props) {
  const [items, setItems] = useState<AutomationSummary[]>([]);
  const [corruptos, setCorruptos] = useState<string[]>([]);
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [editorOpen, setEditorOpen] = useState<{ existing: Automation | null } | null>(null);
  const [historyFor, setHistoryFor] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [list, cat] = await Promise.all([apiAutomations.list(), apiAutomations.catalogo()]);
      setItems(list.items);
      setCorruptos(list.corruptos);
      setCatalog(cat);
    } catch (e) {
      toast.error('Error cargando: ' + (e instanceof Error ? e.message : String(e)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const toggleActivo = async (it: AutomationSummary) => {
    try {
      const full = await apiAutomations.get(it.id);
      await apiAutomations.update(it.id, {
        nombre: full.nombre,
        activo: !full.activo,
        trigger: full.trigger,
        acciones: full.acciones,
        metadatos: full.metadatos,
      });
      toast.success(`${full.nombre} ${!full.activo ? 'activada' : 'pausada'}`);
      refresh();
    } catch (e) {
      toast.error('Error: ' + (e instanceof Error ? e.message : String(e)));
    }
  };

  const ejecutar = async (it: AutomationSummary) => {
    try {
      const r = await apiAutomations.run(it.id);
      toast.success(`Ejecutada: ${r.status} (${r.duration_ms}ms)`);
      refresh();
    } catch (e) {
      toast.error('Error ejecución: ' + (e instanceof Error ? e.message : String(e)));
    }
  };

  const borrar = async (it: AutomationSummary) => {
    if (!confirm(`¿Archivar ${it.nombre}?`)) return;
    try {
      await apiAutomations.remove(it.id);
      toast.success('Archivada');
      refresh();
    } catch (e) {
      toast.error('Error: ' + (e instanceof Error ? e.message : String(e)));
    }
  };

  const editar = async (id: string) => {
    const a = await apiAutomations.get(id);
    setEditorOpen({ existing: a });
  };

  return (
    <div className="cockpit-root cockpit-grid-bg min-h-screen">
      <header className="flex items-center justify-between px-6 py-3 border-b border-cockpit-border bg-cockpit-panel/40 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="cockpit-mono text-[11px] text-cockpit-textDim hover:text-accent-green flex items-center gap-1"
          >
            <ArrowLeft size={14} />
            COCKPIT
          </button>
          <span className="text-cockpit-border">|</span>
          <h1 className="cockpit-mono text-sm font-bold tracking-[0.18em] text-cockpit-text">
            AUTOMATIZACIONES · n8n light
          </h1>
        </div>
        <button
          onClick={() => setEditorOpen({ existing: null })}
          className="cockpit-mono text-[11px] px-3 py-1 rounded bg-accent-green/20 border border-accent-green/40 hover:bg-accent-green/30 text-accent-green flex items-center gap-1.5"
        >
          <Plus size={12} /> NUEVA
        </button>
      </header>

      <main className="px-6 py-4 max-w-5xl mx-auto">
        {loading && <div className="cockpit-mono text-xs text-cockpit-textDim">cargando...</div>}
        {!loading && items.length === 0 && (
          <div className="text-center py-12">
            <div className="cockpit-mono text-sm text-cockpit-textDim">Sin automatizaciones aún.</div>
            <div className="cockpit-mono text-[11px] text-cockpit-dim mt-1">
              Pulsa NUEVA arriba para crear la primera.
            </div>
          </div>
        )}
        {corruptos.length > 0 && (
          <div className="mb-4 px-3 py-2 bg-accent-orange/10 border border-accent-orange/40 rounded text-[11px] cockpit-mono text-accent-orange">
            <div className="font-bold mb-1">YAML CORRUPTOS:</div>
            <ul className="list-disc list-inside">
              {corruptos.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </div>
        )}
        <div className="space-y-2">
          {items.map((it) => (
            <div
              key={it.id}
              className="cockpit-glass rounded-lg p-3 flex items-center gap-3 hover:border-accent-green transition-colors"
            >
              <button
                onClick={() => toggleActivo(it)}
                className={`shrink-0 w-10 h-5 rounded-full transition-colors relative ${
                  it.activo ? 'bg-accent-green' : 'bg-cockpit-border'
                }`}
                aria-label="toggle"
              >
                <span
                  className={`absolute top-0.5 w-4 h-4 rounded-full bg-cockpit-bg transition-transform ${
                    it.activo ? 'translate-x-5' : 'translate-x-0.5'
                  }`}
                />
              </button>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-cockpit-text truncate">{it.nombre}</div>
                <div className="cockpit-mono text-[10px] text-cockpit-textDim flex items-center gap-2 mt-0.5">
                  <span>{it.trigger_tipo}</span>
                  <span>·</span>
                  <span>{it.autor}</span>
                  {it.last_run && (
                    <>
                      <span>·</span>
                      <span className={`inline-block w-2 h-2 rounded-full ${STATUS_DOT[it.last_run.status] || 'bg-cockpit-textDim'}`} />
                      <span>{it.last_run.status} ({it.last_run.duration_ms}ms)</span>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => ejecutar(it)}
                  title="Ejecutar ahora"
                  className="p-1.5 rounded text-cockpit-textDim hover:text-accent-green hover:bg-accent-green/10"
                >
                  <Play size={14} />
                </button>
                <button
                  onClick={() => setHistoryFor(it.id)}
                  title="Historial"
                  className="p-1.5 rounded text-cockpit-textDim hover:text-cockpit-text hover:bg-cockpit-bg/40"
                >
                  <History size={14} />
                </button>
                <button
                  onClick={() => editar(it.id)}
                  title="Editar"
                  className="p-1.5 rounded text-cockpit-textDim hover:text-cockpit-text hover:bg-cockpit-bg/40"
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => borrar(it)}
                  title="Archivar"
                  className="p-1.5 rounded text-cockpit-textDim hover:text-accent-orange hover:bg-accent-orange/10"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>

      {editorOpen && catalog && (
        <AutomationEditor
          catalog={catalog}
          existing={editorOpen.existing}
          onClose={() => setEditorOpen(null)}
          onSaved={() => {
            setEditorOpen(null);
            refresh();
          }}
        />
      )}

      {historyFor && (
        <ExecutionHistoryModal automationId={historyFor} onClose={() => setHistoryFor(null)} />
      )}

      <Toaster position="bottom-right" theme="dark" toastOptions={{ className: 'cockpit-glass !p-3' }} />
    </div>
  );
}
