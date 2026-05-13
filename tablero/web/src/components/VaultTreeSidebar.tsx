/**
 * VaultTreeSidebar — árbol expandible del vault (US8 simplificado).
 *
 * Lazy-load por carpeta. Sin drag-and-drop en esta fase (lo posponemos —
 * el endpoint vault/move no está implementado para mantener el alcance).
 */
import { useCallback, useEffect, useState } from 'react';
import { ChevronRight, Folder, FileText } from 'lucide-react';
import { getVaultTree } from '../lib/api';
import type { VaultNode } from '../lib/types';

interface NodeState {
  expanded: boolean;
  children: VaultNode[] | null;
  loading: boolean;
}

interface Props {
  onSelectFile?: (path: string) => void;
}

export function VaultTreeSidebar({ onSelectFile }: Props) {
  const [rootChildren, setRootChildren] = useState<VaultNode[] | null>(null);
  const [nodes, setNodes] = useState<Record<string, NodeState>>({});
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async (path: string): Promise<VaultNode[] | null> => {
    try {
      const r = await getVaultTree(path);
      return r.children;
    } catch (e) {
      setError(String(e));
      return null;
    }
  }, []);

  useEffect(() => {
    void (async () => {
      const c = await cargar('');
      setRootChildren(c);
    })();
  }, [cargar]);

  async function toggle(path: string) {
    const current = nodes[path] ?? { expanded: false, children: null, loading: false };
    if (current.expanded) {
      setNodes((n) => ({ ...n, [path]: { ...current, expanded: false } }));
      return;
    }
    setNodes((n) => ({ ...n, [path]: { ...current, loading: true } }));
    const children = current.children ?? await cargar(path);
    setNodes((n) => ({
      ...n,
      [path]: { expanded: true, children, loading: false },
    }));
  }

  function renderNode(parent: string, node: VaultNode) {
    const path = parent ? `${parent}/${node.name}` : node.name;
    if (node.type === 'folder') {
      const state = nodes[path];
      const expanded = state?.expanded ?? false;
      return (
        <li key={path}>
          <button
            type="button"
            onClick={() => toggle(path)}
            className="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-sm text-tinta hover:bg-tinta/5"
          >
            <ChevronRight size={12} className={`transition ${expanded ? 'rotate-90' : ''}`} />
            <Folder size={12} className="text-tinta/50" />
            <span>{node.name}</span>
          </button>
          {expanded && state?.children && (
            <ul className="ml-3 border-l border-tinta/10 pl-2">
              {state.children.map((c) => renderNode(path, c))}
            </ul>
          )}
        </li>
      );
    }
    return (
      <li key={path}>
        <button
          type="button"
          onClick={() => onSelectFile?.(path)}
          className="flex w-full items-center gap-1 rounded px-1 py-0.5 text-left text-sm text-tinta/80 hover:bg-tinta/5"
        >
          <FileText size={12} className="text-tinta/40" />
          <span className="truncate">{node.name}</span>
        </button>
      </li>
    );
  }

  if (error) {
    return <div className="p-2 text-xs text-red-700">{error}</div>;
  }
  if (rootChildren === null) {
    return <div className="p-2 text-xs text-tinta/40">Cargando vault…</div>;
  }

  return (
    <nav aria-label="Árbol del vault">
      <ul className="space-y-0.5">
        {rootChildren.map((c) => renderNode('', c))}
      </ul>
    </nav>
  );
}
