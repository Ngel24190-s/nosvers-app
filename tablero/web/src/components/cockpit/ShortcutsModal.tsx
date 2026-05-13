import { useEffect, useState } from 'react';
import { X } from 'lucide-react';

const SHORTCUTS: Array<{ keys: string; description: string }> = [
  { keys: '?', description: 'Mostrar atajos de teclado' },
  { keys: 'g h', description: 'Ir al widget Health (VPS)' },
  { keys: 'g r', description: 'Ir al widget Revenue' },
  { keys: 'g c', description: 'Ir al widget Claude' },
  { keys: 'g a', description: 'Ir a Automatizaciones' },
  { keys: 'Esc', description: 'Cerrar modal / volver al cockpit' },
];

type Listener = () => void;
const listeners = new Set<Listener>();

export function openShortcutsModal() {
  listeners.forEach((l) => l());
}

export function ShortcutsModal() {
  const [open, setOpen] = useState(false);
  const [gPressed, setGPressed] = useState(false);

  useEffect(() => {
    const l = () => setOpen((o) => !o);
    listeners.add(l);
    return () => {
      listeners.delete(l);
    };
  }, []);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;

    const isTyping = () => {
      const el = document.activeElement as HTMLElement | null;
      if (!el) return false;
      const tag = el.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
      if (el.isContentEditable) return true;
      return false;
    };

    function scrollTo(id: string) {
      const node = document.querySelector(`[data-widget="${id}"]`) || document.querySelector(`.react-grid-item:has([data-widget="${id}"])`);
      node?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function onKey(e: KeyboardEvent) {
      if (isTyping()) return;
      // ? muestra modal
      if (e.key === '?' && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        setOpen((o) => !o);
        return;
      }
      if (e.key === 'Escape') {
        setOpen(false);
        return;
      }
      // Secuencia "g h", "g r", "g c", "g a"
      if (e.key.toLowerCase() === 'g' && !e.metaKey && !e.ctrlKey && !e.altKey) {
        setGPressed(true);
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => setGPressed(false), 1200);
        return;
      }
      if (gPressed && !e.metaKey && !e.ctrlKey && !e.altKey) {
        const k = e.key.toLowerCase();
        if (k === 'h') scrollTo('vps');
        else if (k === 'r') scrollTo('revenue');
        else if (k === 'c') scrollTo('claude');
        else if (k === 'a') {
          window.location.hash = 'cockpit/automatizaciones';
        } else return;
        setGPressed(false);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      if (timer) clearTimeout(timer);
    };
  }, [gPressed]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[80] bg-black/60 flex items-center justify-center p-4" onClick={() => setOpen(false)}>
      <div
        className="bg-cockpit-panel border border-cockpit-border rounded-lg p-5 max-w-md w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between mb-3">
          <div className="cockpit-mono text-sm text-cockpit-text">ATAJOS DE TECLADO</div>
          <button onClick={() => setOpen(false)} className="text-cockpit-textDim hover:text-accent-orange">
            <X size={16} />
          </button>
        </header>
        <ul className="space-y-2">
          {SHORTCUTS.map((s) => (
            <li key={s.keys} className="flex items-center justify-between">
              <span className="text-[12px] text-cockpit-text">{s.description}</span>
              <kbd className="cockpit-mono text-[10px] px-1.5 py-0.5 rounded bg-cockpit-bg border border-cockpit-border text-accent-green">
                {s.keys}
              </kbd>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
