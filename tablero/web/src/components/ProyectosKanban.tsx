/**
 * ProyectosKanban — vista kanban con @dnd-kit (US6).
 *
 * 4 columnas (todo / doing / done / blocked) + 5ª "sin_estado" (fallback).
 * Drag-and-drop actualiza el frontmatter del archivo via PATCH.
 */
import { useEffect, useState } from 'react';
import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  TouchSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { ApiError, listProyectos, patchProyecto } from '../lib/api';
import type { Proyecto } from '../lib/types';

type Estado = Proyecto['estado'];

const COLUMNAS: Estado[] = ['todo', 'doing', 'done', 'blocked', 'sin_estado'];

const COLUMN_LABELS: Record<Estado, string> = {
  todo: 'Por hacer',
  doing: 'En curso',
  done: 'Hecho',
  blocked: 'Bloqueado',
  sin_estado: 'Sin estado',
};

function Card({ proyecto }: { proyecto: Proyecto }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: proyecto.slug,
    data: proyecto,
  });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`cursor-grab rounded border border-tinta/10 bg-white p-2 text-xs shadow-sm hover:border-emerald-400 ${
        isDragging ? 'opacity-50' : ''
      }`}
    >
      <p className="font-medium text-tinta">{proyecto.titulo || proyecto.slug}</p>
      {proyecto.responsable && (
        <p className="mt-1 text-tinta/50">{proyecto.responsable}</p>
      )}
      {proyecto.deadline && (
        <p className="text-tinta/50">⏰ {proyecto.deadline}</p>
      )}
      {Array.isArray(proyecto.etiquetas) && proyecto.etiquetas.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1">
          {proyecto.etiquetas.map((t) => (
            <span key={t} className="rounded bg-tinta/5 px-1 py-0.5 text-[10px] text-tinta/60">
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function Column({ estado, proyectos }: { estado: Estado; proyectos: Proyecto[] }) {
  const { isOver, setNodeRef } = useDroppable({ id: estado });
  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[200px] flex-col rounded-md border bg-cream/40 p-2 transition ${
        isOver ? 'border-emerald-400 bg-emerald-50' : 'border-tinta/10'
      }`}
    >
      <h3 className="mb-2 flex items-center justify-between text-xs font-medium uppercase text-tinta/60">
        <span>{COLUMN_LABELS[estado]}</span>
        <span className="rounded-full bg-tinta/10 px-1.5 text-[10px]">{proyectos.length}</span>
      </h3>
      <div className="flex flex-1 flex-col gap-1.5">
        {proyectos.length === 0 ? (
          <p className="px-2 py-3 text-center text-[10px] text-tinta/30">vacío</p>
        ) : (
          proyectos.map((p) => <Card key={p.slug} proyecto={p} />)
        )}
      </div>
    </div>
  );
}

export function ProyectosKanban() {
  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 8 } }),
  );

  useEffect(() => {
    void recargar();
  }, []);

  async function recargar() {
    setLoading(true);
    setError(null);
    try {
      const r = await listProyectos();
      setProyectos(r.proyectos);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function onDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const proyecto = proyectos.find((p) => p.slug === active.id);
    if (!proyecto) return;
    const nuevoEstado = over.id as Estado;
    if (proyecto.estado === nuevoEstado) return;
    if (nuevoEstado === 'sin_estado') return; // sin_estado no es target válido

    // Optimistic update
    setProyectos((prev) =>
      prev.map((p) => (p.slug === proyecto.slug ? { ...p, estado: nuevoEstado } : p)),
    );

    try {
      const ifMatch = proyecto.modified_at ?? '';
      const updated = await patchProyecto(proyecto.slug, ifMatch, { estado: nuevoEstado });
      setProyectos((prev) =>
        prev.map((p) => (p.slug === proyecto.slug ? { ...updated, estado: updated.estado } : p)),
      );
    } catch (e) {
      // Rollback
      setProyectos((prev) =>
        prev.map((p) => (p.slug === proyecto.slug ? proyecto : p)),
      );
      if (e instanceof ApiError) {
        setError(`No pude mover "${proyecto.titulo}": ${e.detalle ?? e.code}`);
      } else {
        setError(String(e));
      }
    }
  }

  if (loading) return <p className="text-sm text-tinta/50">Cargando proyectos…</p>;

  const porColumna: Record<Estado, Proyecto[]> = {
    todo: [], doing: [], done: [], blocked: [], sin_estado: [],
  };
  for (const p of proyectos) {
    porColumna[p.estado].push(p);
  }

  return (
    <div className="space-y-3">
      <h2 className="font-display text-lg">Proyectos NosVers</h2>
      {error && (
        <div className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-700">{error}</div>
      )}
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {COLUMNAS.map((c) => (
            <Column key={c} estado={c} proyectos={porColumna[c]} />
          ))}
        </div>
      </DndContext>
    </div>
  );
}
