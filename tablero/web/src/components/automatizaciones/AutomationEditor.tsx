import { useCallback, useEffect, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MarkerType,
  type Edge,
  type Node,
  type NodeProps,
  applyEdgeChanges,
  applyNodeChanges,
  type EdgeChange,
  type NodeChange,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, Save, X, Trash2 } from 'lucide-react';
import { JsonSchemaForm } from './JsonSchemaForm';
import { YamlPreview } from './YamlPreview';
import { TestRunModal } from './TestRunModal';
import { exportToYaml } from './lib/yamlExport';
import {
  apiAutomations,
  type Automation,
  type AutomationCreate,
  type Catalog,
} from './lib/apiAutomations';

type NodeKind = 'trigger' | 'action';
interface NodeData {
  kind: NodeKind;
  tipo: string;
  values: Record<string, unknown>;
  label: string;
}

function customNodeView({ data, selected }: NodeProps<NodeData>) {
  const accent = data.kind === 'trigger' ? 'text-accent-orange' : 'text-accent-green';
  return (
    <div
      className={`rounded-lg border ${selected ? 'border-accent-green' : 'border-cockpit-border'} bg-cockpit-panel px-3 py-2 text-xs min-w-[140px]`}
    >
      <div className={`cockpit-mono text-[10px] ${accent}`}>
        {data.kind === 'trigger' ? 'TRIGGER' : 'ACTION'}
      </div>
      <div className="text-cockpit-text mt-0.5 font-medium">{data.label || data.tipo}</div>
    </div>
  );
}

const nodeTypes = { custom: customNodeView };

interface EditorProps {
  catalog: Catalog;
  existing?: Automation | null;
  onClose: () => void;
  onSaved: () => void;
}

export function AutomationEditor({ catalog, existing, onClose, onSaved }: EditorProps) {
  const [nombre, setNombre] = useState(existing?.nombre ?? 'Nueva automatización');
  const [activo, setActivo] = useState(existing?.activo ?? false);
  const [nodes, setNodes] = useState<Node<NodeData>[]>(() => {
    if (existing) {
      const triggerNode: Node<NodeData> = {
        id: 'trigger',
        type: 'custom',
        position: { x: 60, y: 80 },
        data: {
          kind: 'trigger',
          tipo: existing.trigger.tipo,
          values: { ...existing.trigger },
          label: catalog.triggers[existing.trigger.tipo]?.label || existing.trigger.tipo,
        },
      };
      const actionNodes: Node<NodeData>[] = existing.acciones.map((a, i) => ({
        id: `action_${i}`,
        type: 'custom',
        position: { x: 380 + i * 220, y: 80 },
        data: {
          kind: 'action',
          tipo: a.tipo,
          values: { ...a },
          label: catalog.actions[a.tipo]?.label || a.tipo,
        },
      }));
      return [triggerNode, ...actionNodes];
    }
    return [
      {
        id: 'trigger',
        type: 'custom',
        position: { x: 60, y: 80 },
        data: { kind: 'trigger', tipo: '', values: {}, label: 'Elegir trigger' },
      },
    ];
  });
  const [edges, setEdges] = useState<Edge[]>(() => {
    if (existing) {
      const e: Edge[] = [];
      const ids = ['trigger', ...existing.acciones.map((_, i) => `action_${i}`)];
      for (let i = 0; i < ids.length - 1; i++) {
        e.push({
          id: `e_${i}`,
          source: ids[i],
          target: ids[i + 1],
          markerEnd: { type: MarkerType.ArrowClosed },
        });
      }
      return e;
    }
    return [];
  });
  const [selected, setSelected] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testOpen, setTestOpen] = useState(false);

  const onNodesChange = useCallback((c: NodeChange[]) => setNodes((nds) => applyNodeChanges(c, nds)), []);
  const onEdgesChange = useCallback((c: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(c, eds)), []);

  const addAction = (tipo: string) => {
    const i = nodes.filter((n) => n.data.kind === 'action').length;
    const id = `action_${Date.now()}_${i}`;
    const newNode: Node<NodeData> = {
      id,
      type: 'custom',
      position: { x: 380 + i * 220, y: 80 + (i % 2) * 60 },
      data: {
        kind: 'action',
        tipo,
        values: { tipo },
        label: catalog.actions[tipo]?.label || tipo,
      },
    };
    // conectar con el último nodo
    const last = [...nodes].pop();
    setNodes([...nodes, newNode]);
    if (last) {
      setEdges([
        ...edges,
        {
          id: `e_${last.id}_${id}`,
          source: last.id,
          target: id,
          markerEnd: { type: MarkerType.ArrowClosed },
        },
      ]);
    }
    setSelected(id);
  };

  const setTrigger = (tipo: string) => {
    setNodes((nds) =>
      nds.map((n) =>
        n.id === 'trigger'
          ? {
              ...n,
              data: {
                kind: 'trigger',
                tipo,
                values: { tipo },
                label: catalog.triggers[tipo]?.label || tipo,
              },
            }
          : n,
      ),
    );
    setSelected('trigger');
  };

  const updateValues = (id: string, vals: Record<string, unknown>) => {
    setNodes((nds) =>
      nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, values: { ...vals, tipo: n.data.tipo } } } : n)),
    );
  };

  const removeNode = (id: string) => {
    if (id === 'trigger') return;
    setNodes((nds) => nds.filter((n) => n.id !== id));
    setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
    setSelected(null);
  };

  const selectedNode = nodes.find((n) => n.id === selected);

  const buildPayload = (): AutomationCreate | null => {
    const triggerNode = nodes.find((n) => n.id === 'trigger');
    if (!triggerNode || !triggerNode.data.tipo) {
      setError('Falta el trigger');
      return null;
    }
    const acciones = nodes.filter((n) => n.data.kind === 'action').map((n) => n.data.values);
    if (acciones.length === 0) {
      setError('Añade al menos una acción');
      return null;
    }
    return {
      nombre,
      activo,
      trigger: triggerNode.data.values as { tipo: string },
      acciones: acciones as Array<{ tipo: string }>,
    };
  };

  const yaml = useMemo(() => {
    const triggerNode = nodes.find((n) => n.id === 'trigger');
    return exportToYaml({
      nombre,
      activo,
      trigger: triggerNode?.data.tipo ? (triggerNode.data.values as Record<string, unknown>) : null,
      acciones: nodes.filter((n) => n.data.kind === 'action').map((n) => n.data.values as Record<string, unknown>),
    });
  }, [nodes, nombre, activo]);

  const save = async () => {
    setError(null);
    const payload = buildPayload();
    if (!payload) return;
    setSaving(true);
    try {
      if (existing) {
        await apiAutomations.update(existing.id, payload);
      } else {
        await apiAutomations.create(payload);
      }
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-cockpit-bg/95 backdrop-blur-md flex flex-col">
      <header className="flex items-center justify-between px-4 py-2 border-b border-cockpit-border bg-cockpit-panel/50">
        <div className="flex items-center gap-3">
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            className="bg-transparent text-cockpit-text text-sm font-bold cockpit-mono px-2 py-1 outline-none border-b border-transparent focus:border-accent-green"
          />
          <label className="flex items-center gap-1.5 text-[11px] cockpit-mono text-cockpit-textDim">
            <input type="checkbox" checked={activo} onChange={(e) => setActivo(e.target.checked)} />
            ACTIVO
          </label>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setTestOpen(true)}
            className="px-3 py-1 rounded bg-cockpit-panel border border-cockpit-border hover:border-accent-orange text-[11px] cockpit-mono text-cockpit-text flex items-center gap-1.5"
          >
            <Play size={12} /> TEST RUN
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="px-3 py-1 rounded bg-accent-green/20 border border-accent-green/40 hover:bg-accent-green/30 text-[11px] cockpit-mono text-accent-green flex items-center gap-1.5"
          >
            <Save size={12} /> {saving ? 'GUARDANDO...' : 'GUARDAR'}
          </button>
          <button
            onClick={onClose}
            className="p-1 rounded text-cockpit-textDim hover:text-accent-orange"
            aria-label="cerrar"
          >
            <X size={16} />
          </button>
        </div>
      </header>

      {error && (
        <div className="bg-accent-orange/20 text-accent-orange text-xs cockpit-mono px-4 py-2 border-b border-accent-orange/40">
          {error}
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={(_, n) => setSelected(n.id)}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background gap={20} size={1} />
            <Controls />
          </ReactFlow>
          {/* YAML preview overlay */}
          <div className="absolute bottom-2 left-2 right-2 max-h-[40%]">
            <YamlPreview yaml={yaml} height={180} />
          </div>
        </div>

        {/* Sidebar derecha */}
        <aside className="w-[320px] border-l border-cockpit-border bg-cockpit-panel/30 overflow-y-auto">
          {selectedNode ? (
            <NodeInspector
              key={selectedNode.id}
              node={selectedNode}
              catalog={catalog}
              onChangeTipo={(tipo) => {
                if (selectedNode.data.kind === 'trigger') setTrigger(tipo);
                else {
                  setNodes((nds) =>
                    nds.map((n) =>
                      n.id === selectedNode.id
                        ? {
                            ...n,
                            data: { ...n.data, tipo, values: { tipo }, label: catalog.actions[tipo]?.label || tipo },
                          }
                        : n,
                    ),
                  );
                }
              }}
              onChangeValues={(v) => updateValues(selectedNode.id, v)}
              onRemove={() => removeNode(selectedNode.id)}
            />
          ) : (
            <div className="p-4 text-[11px] cockpit-mono text-cockpit-textDim">
              Selecciona un nodo para editarlo.
            </div>
          )}

          <div className="border-t border-cockpit-border p-3">
            <div className="text-[10px] cockpit-mono text-cockpit-textDim mb-2">AÑADIR ACCIÓN</div>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(catalog.actions).map(([tipo, meta]) => (
                <button
                  key={tipo}
                  onClick={() => addAction(tipo)}
                  disabled={!meta.available}
                  title={meta.reason}
                  className={`text-[10px] cockpit-mono px-2 py-1.5 rounded border text-left transition-colors ${
                    meta.available
                      ? 'bg-cockpit-bg/40 border-cockpit-border text-cockpit-text hover:border-accent-green'
                      : 'bg-cockpit-bg/20 border-cockpit-border/50 text-cockpit-dim cursor-not-allowed'
                  }`}
                >
                  {meta.label}
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {testOpen && (
        <TestRunModal
          automation={existing}
          draftPayload={buildPayload()}
          onClose={() => setTestOpen(false)}
        />
      )}
    </div>
  );
}

interface NodeInspectorProps {
  node: Node<NodeData>;
  catalog: Catalog;
  onChangeTipo: (tipo: string) => void;
  onChangeValues: (v: Record<string, unknown>) => void;
  onRemove: () => void;
}

function NodeInspector({ node, catalog, onChangeTipo, onChangeValues, onRemove }: NodeInspectorProps) {
  const isTrigger = node.data.kind === 'trigger';
  const tipoOptions = Object.entries(isTrigger ? catalog.triggers : catalog.actions);
  const tipoMeta = node.data.tipo
    ? isTrigger
      ? catalog.triggers[node.data.tipo]
      : catalog.actions[node.data.tipo]
    : null;
  return (
    <div className="p-3">
      <div className="flex items-center justify-between mb-3">
        <div className="cockpit-mono text-[10px] text-cockpit-textDim">
          {isTrigger ? 'TRIGGER' : 'ACCIÓN'}
        </div>
        {!isTrigger && (
          <button
            onClick={onRemove}
            className="p-1 text-cockpit-textDim hover:text-accent-orange"
            aria-label="eliminar"
          >
            <Trash2 size={12} />
          </button>
        )}
      </div>
      <div className="mb-3">
        <label className="block text-[11px] cockpit-mono text-cockpit-textDim mb-1">TIPO</label>
        <select
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text"
          value={node.data.tipo}
          onChange={(e) => onChangeTipo(e.target.value)}
        >
          <option value="">— elegir —</option>
          {tipoOptions.map(([tipo, meta]) => (
            <option key={tipo} value={tipo} disabled={!meta.available}>
              {meta.label}
              {!meta.available && ' (no disponible)'}
            </option>
          ))}
        </select>
      </div>
      {tipoMeta?.schema && (
        <JsonSchemaForm
          schema={tipoMeta.schema as Parameters<typeof JsonSchemaForm>[0]['schema']}
          value={node.data.values}
          onChange={(v) => onChangeValues(v)}
        />
      )}
      {tipoMeta?.reason && (
        <div className="mt-2 text-[10px] text-accent-orange cockpit-mono">{tipoMeta.reason}</div>
      )}
    </div>
  );
}
