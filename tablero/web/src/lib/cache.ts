import { get, set, del, keys } from 'idb-keyval';
import type { NoteFull, TimelineEntry } from './types';

const TIMELINE_KEY = 'timeline:last';
const NOTE_PREFIX = 'note:';
const MAX_NOTES = 30;

export async function getCachedTimeline(): Promise<TimelineEntry[] | null> {
  try {
    return (await get(TIMELINE_KEY)) ?? null;
  } catch {
    return null;
  }
}

export async function setCachedTimeline(entries: TimelineEntry[]): Promise<void> {
  try {
    await set(TIMELINE_KEY, entries.slice(0, MAX_NOTES));
  } catch {
    /* IndexedDB unavailable — ignore */
  }
}

export async function getCachedNote(path: string): Promise<NoteFull | null> {
  try {
    return (await get(NOTE_PREFIX + path)) ?? null;
  } catch {
    return null;
  }
}

export async function setCachedNote(path: string, note: NoteFull): Promise<void> {
  try {
    await set(NOTE_PREFIX + path, note);
    // Best-effort prune: keep the 30 most recent note keys.
    const allKeys = await keys();
    const noteKeys = allKeys.filter((k): k is string => typeof k === 'string' && k.startsWith(NOTE_PREFIX));
    if (noteKeys.length > MAX_NOTES) {
      // No mtime stored alongside the key — drop the lexicographically smallest as a cheap heuristic.
      const overflow = noteKeys.sort().slice(0, noteKeys.length - MAX_NOTES);
      await Promise.all(overflow.map((k) => del(k)));
    }
  } catch {
    /* ignore */
  }
}
