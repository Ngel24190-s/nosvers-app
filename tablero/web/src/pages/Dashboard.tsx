import { useCallback, useEffect, useMemo, useState } from 'react';
import { LogOut } from 'lucide-react';
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
} from '../lib/types';
import { AuthorChip } from '../components/AuthorChip';
import { FilterBar } from '../components/FilterBar';
import { SearchBar } from '../components/SearchBar';
import { TimelineList } from '../components/TimelineList';
import { TimelineItem } from '../components/TimelineItem';
import { NoteDetail } from '../components/NoteDetail';
import { OfflineBanner } from '../components/OfflineBanner';
import { getCachedTimeline, setCachedTimeline, setCachedNote, getCachedNote } from '../lib/cache';

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

  // Timeline fetch (re-runs on filter change, debounced)
  useEffect(() => {
    writeFiltersToURL(filters);
    let cancelled = false;
    const handle = window.setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await getTimeline(filters);
        if (cancelled) return;
        setEntries(r.entradas);
        setLoading(false);
        void setCachedTimeline(r.entradas);
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError && e.isAuthError) {
          window.location.reload();
          return;
        }
        // Network error fallback to cache
        const cached = await getCachedTimeline();
        if (cached) setEntries(cached);
        setError(String(e));
        setLoading(false);
      }
    }, 150);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [filters]);

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
    setSelectedPath(path);
    setSelectedNote(null);
    // optimistic cache hit
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
      // keep cached if any; else display a transient error placeholder
      if (!cached) {
        setSelectedNote(null);
        setError(String(e));
      }
    }
  }, []);

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

  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-30 bg-cream/95 backdrop-blur border-b border-tinta/10">
        <div className="mx-auto max-w-3xl px-4 py-3 flex items-center gap-3">
          <h1 className="font-display text-xl">Tablero</h1>
          <SearchBar onSearch={onSearch} />
          <span className="ml-auto flex items-center gap-2">
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

      <OfflineBanner visible={offline} />

      <main className="flex-1 mx-auto w-full max-w-3xl px-4 py-4 flex flex-col gap-4">
        {!showSearch && <FilterBar filters={filters} onChange={setFilters} />}

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
          <TimelineList entries={entries} onSelect={(e) => openNote(e.path)} />
        )}
      </main>

      <NoteDetail
        nota={selectedNote}
        onClose={() => {
          setSelectedNote(null);
          setSelectedPath(null);
        }}
      />
      {selectedPath && !selectedNote && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-tinta text-cream text-sm px-3 py-1.5 shadow">
          Abriendo nota…
        </div>
      )}
    </div>
  );
}
