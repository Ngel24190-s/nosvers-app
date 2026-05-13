import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogOut, Plus, Edit3, Command as CommandIcon, Layout, Trello, Archive, Folder } from 'lucide-react';
import { ApiError, getBuscar, getNota, getTimeline } from '../lib/api';
import { clearToken } from '../lib/auth';
import {
  DEFAULT_FILTERS,
  type AutorFiltro,
  type Etiqueta,
  type NoteFull,
  type SearchHit,
  type TimelineEntry,
  type TimelineFilters,
  type Vista,
} from '../lib/types';
import { AuthorChip } from '../components/AuthorChip';
import { FilterBar } from '../components/FilterBar';
import { SearchBar } from '../components/SearchBar';
import { TimelineList } from '../components/TimelineList';
import { TimelineItem } from '../components/TimelineItem';
import { NoteDetail } from '../components/NoteDetail';
import { NoteEditor } from '../components/NoteEditor';
import { OfflineBanner } from '../components/OfflineBanner';
import { CaptureModal } from '../components/CaptureModal';
import { CommandPalette } from '../components/CommandPalette';
import { ViewSwitcher } from '../components/ViewSwitcher';
import { TableView } from '../components/TableView';
import { KanbanByTagView } from '../components/KanbanByTagView';
import { CalendarMonthView } from '../components/CalendarMonthView';
import { GalleryView } from '../components/GalleryView';
import { ArchiveDialog } from '../components/ArchiveDialog';
import { PapeleraView } from '../components/PapeleraView';
import { ProyectosKanban } from '../components/ProyectosKanban';
import { VaultTreeSidebar } from '../components/VaultTreeSidebar';
import { getCachedTimeline, setCachedTimeline, setCachedNote, getCachedNote } from '../lib/cache';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';
import { useVistaPersist } from '../hooks/useVistaPersist';

type Modo = 'timeline' | 'proyectos' | 'papelera';

interface Props {
  identitySub: 'angel' | 'africa';
}

function filtersFromURL(): TimelineFilters {
  const p = new URLSearchParams(window.location.search);
  const autor = (p.get('autor') as AutorFiltro | null) ?? DEFAULT_FILTERS.autor;
  const etiqueta = (p.get('etiqueta') as Etiqueta | null) ?? '';
  const desde = p.get('desde') ?? '';
  const hasta = p.get('hasta') ?? '';
  return { autor, etiqueta, desde, hasta };
}

function writeFiltersToURL(f: TimelineFilters) {
  const p = new URLSearchParams();
  if (f.autor && f.autor !== 'ambos') p.set('autor', f.autor);
  if (f.etiqueta) p.set('etiqueta', f.etiqueta);
  if (f.desde) p.set('desde', f.desde);
  if (f.hasta) p.set('hasta', f.hasta);
  const qs = p.toString();
  const next = qs ? `?${qs}` : window.location.pathname;
  window.history.replaceState(null, '', next);
}

export function Dashboard({ identitySub }: Props) {
  const [filters, setFilters] = useState<TimelineFilters>(() => filtersFromURL());
  const [entries, setEntries] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(!navigator.onLine);

  const [query, setQuery] = useState('');
  const [searchHits, setSearchHits] = useState<SearchHit[] | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [selectedNote, setSelectedNote] = useState<NoteFull | null>(null);
  const [editing, setEditing] = useState(false);

  // Fase B+C state
  const [captureOpen, setCaptureOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [vista, setVista] = useVistaPersist();
  const [modo, setModo] = useState<Modo>('timeline');
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Online/offline tracker
  useEffect(() => {
    const on = () => setOffline(false);
    const off = () => setOffline(true);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => {
      window.removeEventListener('online', on);
      window.removeEventListener('offline', off);
    };
  }, []);

  // Refresh timeline
  const refreshTimeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getTimeline(filters);
      setEntries(r.entradas);
      setLoading(false);
      void setCachedTimeline(r.entradas);
    } catch (e) {
      if (e instanceof ApiError && e.isAuthError) {
        window.location.reload();
        return;
      }
      const cached = await getCachedTimeline();
      if (cached) setEntries(cached);
      setError(String(e));
      setLoading(false);
    }
  }, [filters]);

  // Timeline fetch (re-runs on filter change, debounced)
  useEffect(() => {
    writeFiltersToURL(filters);
    const handle = window.setTimeout(() => {
      void refreshTimeline();
    }, 150);
    return () => window.clearTimeout(handle);
  }, [filters, refreshTimeline]);

  // Search
  const onSearch = useCallback(async (q: string) => {
    setQuery(q);
    if (!q) {
      setSearchHits(null);
      setSearchLoading(false);
      return;
    }
    setSearchLoading(true);
    try {
      const r = await getBuscar({ q });
      setSearchHits(r.resultados);
    } catch (e) {
      if (e instanceof ApiError && e.isAuthError) {
        window.location.reload();
        return;
      }
      setSearchHits([]);
    } finally {
      setSearchLoading(false);
    }
  }, []);

  // Open note detail
  const openNote = useCallback(async (path: string) => {
    setEditing(false);
    setSelectedPath(path);
    setSelectedNote(null);
    const cached = await getCachedNote(path);
    if (cached) setSelectedNote(cached);
    try {
      const r = await getNota(path);
      setSelectedNote(r.nota);
      void setCachedNote(path, r.nota);
    } catch (e) {
      if (e instanceof ApiError && e.isAuthError) {
        window.location.reload();
        return;
      }
      if (!cached) {
        setSelectedNote(null);
        setError(String(e));
      }
    }
  }, []);

  // ─── Atajos globales ───────────────────────────────────────────────────────
  useKeyboardShortcut('Mod+N', () => {
    setPaletteOpen(false);
    setCaptureOpen(true);
  });

  useKeyboardShortcut('Mod+K', () => {
    setCaptureOpen(false);
    setPaletteOpen(true);
  });

  // Concurrency token de la nota seleccionada (modified_at o ts)
  const concurrencyToken = useMemo(() => {
    if (!selectedNote) return '';
    const fm = selectedNote.frontmatter as { ts?: string; modified_at?: string };
    return fm.modified_at ?? fm.ts ?? '';
  }, [selectedNote]);

  const showSearch = Boolean(query);
  const hitsAsEntries = useMemo(
    () =>
      (searchHits ?? []).map<TimelineEntry & { fragmento: string }>((h) => ({
        path: `dia/${h.fecha}.md#${h.ts}`,
        fecha: h.fecha,
        ts: h.ts,
        autor: h.autor,
        etiqueta: h.etiqueta,
        origen: h.origen,
        titulo: null,
        preview: '',
        tiene_audio: false,
        metadata_incompleta: false,
        fragmento: h.fragmento,
      })),
    [searchHits],
  );

  function logout() {
    clearToken();
    window.location.reload();
  }

  function handleSelectDay(fecha: string) {
    // Filtrar el timeline a un día concreto: setear rango desde=hasta=fecha y volver a Lista
    setFilters((f) => ({ ...f, desde: fecha, hasta: fecha }));
    setVista('lista');
  }

  function renderVista() {
    if (vista === 'lista') return <TimelineList entries={entries} onSelect={(e) => openNote(e.path)} />;
    if (vista === 'tabla') return <TableView entradas={entries} onSelect={(e) => openNote(e.path)} />;
    if (vista === 'kanban') return <KanbanByTagView entradas={entries} onSelect={(e) => openNote(e.path)} />;
    if (vista === 'calendario') return <CalendarMonthView entradas={entries} onSelectDay={handleSelectDay} />;
    if (vista === 'galeria') return <GalleryView entradas={entries} onSelect={(e) => openNote(e.path)} />;
    return null;
  }

  function navFile(path: string) {
    // path es relativo a knowledge_base/; abrir si es nota de dia/
    if (path.startsWith('dia/') && path.endsWith('.md') && !path.includes('archivo/')) {
      // Recordatorio: aún sin selector por ts dentro del día via tree → solo abre el primer día
      // En MVP redirigimos al backend timeline; aquí solo cerramos el drawer
      setSidebarOpen(false);
    }
  }

  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-30 bg-cream/95 backdrop-blur border-b border-tinta/10">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-3">
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            aria-label="Sidebar vault"
            className="rounded-full p-1.5 text-tinta/60 hover:bg-tinta/5 hover:text-tinta"
            title="Árbol del vault"
          >
            <Folder size={16} />
          </button>
          <h1 className="font-display text-xl">Tablero</h1>

          {/* Mode switcher */}
          <nav className="hidden sm:flex items-center gap-1">
            <button
              type="button"
              onClick={() => setModo('timeline')}
              className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs ${
                modo === 'timeline' ? 'bg-emerald-600 text-white' : 'text-tinta/70 hover:bg-tinta/5'
              }`}
            >
              <Layout size={12} /> Timeline
            </button>
            <button
              type="button"
              onClick={() => setModo('proyectos')}
              className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs ${
                modo === 'proyectos' ? 'bg-emerald-600 text-white' : 'text-tinta/70 hover:bg-tinta/5'
              }`}
            >
              <Trello size={12} /> Proyectos
            </button>
            <button
              type="button"
              onClick={() => setModo('papelera')}
              className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs ${
                modo === 'papelera' ? 'bg-emerald-600 text-white' : 'text-tinta/70 hover:bg-tinta/5'
              }`}
            >
              <Archive size={12} /> Papelera
            </button>
          </nav>

          {modo === 'timeline' && <SearchBar onSearch={onSearch} />}
          <span className="ml-auto flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              title="Búsqueda global (Ctrl+K)"
              aria-label="Abrir paleta"
              className="rounded-full p-1.5 text-tinta/60 hover:bg-tinta/5 hover:text-tinta"
            >
              <CommandIcon size={16} />
            </button>
            <button
              type="button"
              onClick={() => setCaptureOpen(true)}
              title="Capturar nota (Ctrl+N)"
              aria-label="Capturar"
              className="rounded-full bg-emerald-600 p-1.5 text-white hover:bg-emerald-700"
            >
              <Plus size={16} />
            </button>
            <AuthorChip autor={identitySub} />
            <button
              type="button"
              onClick={logout}
              className="rounded-full p-1.5 text-tinta/60 hover:bg-tinta/5 hover:text-tinta"
              aria-label="salir"
              title="salir"
            >
              <LogOut size={16} />
            </button>
          </span>
        </div>
      </header>

      {/* Sidebar drawer */}
      {sidebarOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-tinta/20"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
          <aside className="fixed left-0 top-[57px] z-40 h-[calc(100vh-57px)] w-72 overflow-y-auto border-r border-tinta/10 bg-cream/95 p-3 shadow-lg">
            <h2 className="mb-2 text-xs font-medium uppercase text-tinta/60">knowledge_base/</h2>
            <VaultTreeSidebar onSelectFile={navFile} />
          </aside>
        </>
      )}

      <OfflineBanner visible={offline} />

      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-4 flex flex-col gap-4">
        {modo === 'proyectos' ? (
          <ProyectosKanban />
        ) : modo === 'papelera' ? (
          <PapeleraView onRestaurada={() => void refreshTimeline()} />
        ) : (
          <>
        {!showSearch && (
          <div className="flex flex-wrap items-center justify-between gap-3">
            <FilterBar filters={filters} onChange={setFilters} />
            <ViewSwitcher vista={vista} onChange={setVista} />
          </div>
        )}

        {showSearch ? (
          <section>
            <h2 className="font-display text-lg mb-2">
              Resultados {searchLoading && <span className="text-sm text-tinta/40 ml-2">buscando…</span>}
            </h2>
            {searchHits && searchHits.length === 0 && !searchLoading ? (
              <p className="text-sm text-tinta/60">
                Sin resultados para <span className="font-medium">{query}</span>.
              </p>
            ) : (
              <ul className="flex flex-col gap-3">
                {hitsAsEntries.map((h) => (
                  <li key={h.path}>
                    <TimelineItem entry={h} onSelect={(e) => openNote(e.path)} snippet={h.fragmento} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        ) : loading ? (
          <ul className="flex flex-col gap-3" aria-busy="true">
            {Array.from({ length: 3 }).map((_, i) => (
              <li key={i} className="skeleton h-24" />
            ))}
          </ul>
        ) : error ? (
          <div className="rounded-2xl border border-africa/30 bg-white p-4 text-sm">
            <p className="font-medium text-africa">No pude cargar el timeline.</p>
            <p className="text-tinta/70 mt-1">{error}</p>
          </div>
        ) : (
          renderVista()
        )}
        </>
        )}
      </main>

      {/* Detail panel — read-only */}
      {!editing && selectedNote && (
        <NoteDetail
          nota={selectedNote}
          onClose={() => {
            setSelectedNote(null);
            setSelectedPath(null);
          }}
          onArchive={() => setArchiveOpen(true)}
        />
      )}

      {/* Edit button overlay when reading */}
      {!editing && selectedNote && (
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="fixed bottom-6 right-6 z-[60] flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-2 text-sm text-white shadow-lg hover:bg-emerald-700"
        >
          <Edit3 size={14} />
          Editar
        </button>
      )}

      {/* Edit panel */}
      {editing && selectedNote && (
        <div className="fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-tinta/30 backdrop-blur-sm" onClick={() => setEditing(false)} />
          <aside className="relative ml-auto h-full w-full bg-cream shadow-2xl sm:max-w-3xl">
            <NoteEditor
              nota={selectedNote}
              concurrencyToken={concurrencyToken}
              onCancel={() => setEditing(false)}
              onSaved={async () => {
                setEditing(false);
                // Refrescar timeline + nota
                if (selectedPath) {
                  const r = await getNota(selectedPath).catch(() => null);
                  if (r) {
                    setSelectedNote(r.nota);
                    void setCachedNote(selectedPath, r.nota);
                  }
                }
                void refreshTimeline();
              }}
            />
          </aside>
        </div>
      )}

      {selectedPath && !selectedNote && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-tinta text-cream text-sm px-3 py-1.5 shadow">
          Abriendo nota…
        </div>
      )}

      {/* US1: capture modal */}
      <CaptureModal
        open={captureOpen}
        onClose={() => setCaptureOpen(false)}
        onCaptured={() => {
          void refreshTimeline();
        }}
      />

      {/* US5: command palette */}
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        onSelectHit={(h) => openNote(`dia/${h.fecha}.md#${h.ts}`)}
        onAction={(a) => {
          if (a === 'capturar') {
            setCaptureOpen(true);
          } else if (a.startsWith('vista:')) {
            setVista(a.slice('vista:'.length) as Vista);
          }
        }}
      />

      {/* US3: archive dialog */}
      <ArchiveDialog
        open={archiveOpen}
        notePath={selectedPath}
        concurrencyToken={concurrencyToken}
        onArchived={() => {
          setArchiveOpen(false);
          setSelectedNote(null);
          setSelectedPath(null);
          void refreshTimeline();
        }}
        onCancel={() => setArchiveOpen(false)}
      />
    </div>
  );
}
