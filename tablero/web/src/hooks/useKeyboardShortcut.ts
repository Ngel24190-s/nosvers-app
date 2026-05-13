/**
 * useKeyboardShortcut — registra un atajo global de teclado con detección OS (D-015).
 *
 * Convención: la key se especifica como `Ctrl+K`, `Cmd+N`, `Ctrl+N`, `Mod+K`...
 * `Mod+X` o `Ctrl+X` o `Cmd+X` matchean indistintamente `metaKey || ctrlKey`
 * (un usuario macOS pulsa Cmd, un usuario Linux/Windows pulsa Ctrl).
 *
 * Para evitar disparar dentro de inputs activos, por defecto NO se dispara si
 * `document.activeElement` es un input/textarea/contentEditable. Override con
 * `{ allowInInputs: true }` (útil para `Esc`).
 */
import { useEffect } from 'react';

interface Options {
  allowInInputs?: boolean;
  preventDefault?: boolean;
}

function parseShortcut(shortcut: string) {
  const parts = shortcut.split('+').map((p) => p.trim().toLowerCase());
  const key = parts[parts.length - 1];
  const mods = parts.slice(0, -1);
  return {
    key,
    needsMod: mods.includes('ctrl') || mods.includes('cmd') || mods.includes('mod') || mods.includes('meta'),
    needsShift: mods.includes('shift'),
    needsAlt: mods.includes('alt'),
  };
}

function isTypingInElement(el: Element | null): boolean {
  if (!el) return false;
  const tag = el.tagName.toLowerCase();
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true;
  if ((el as HTMLElement).isContentEditable) return true;
  return false;
}

export function useKeyboardShortcut(
  shortcut: string,
  handler: (e: KeyboardEvent) => void,
  options: Options = {},
) {
  useEffect(() => {
    const { key, needsMod, needsShift, needsAlt } = parseShortcut(shortcut);
    const allowInInputs = options.allowInInputs ?? false;
    const preventDefault = options.preventDefault ?? true;

    function onKey(e: KeyboardEvent) {
      if (!allowInInputs && isTypingInElement(document.activeElement)) return;
      if (e.key.toLowerCase() !== key) return;
      const hasMod = e.metaKey || e.ctrlKey;
      if (needsMod !== hasMod) return;
      if (needsShift !== e.shiftKey) return;
      if (needsAlt !== e.altKey) return;
      if (preventDefault) e.preventDefault();
      handler(e);
    }

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [shortcut, handler, options.allowInInputs, options.preventDefault]);
}
