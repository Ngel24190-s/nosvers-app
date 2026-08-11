/* ============================================================================
   SAUVEGARDE LOCALE DU BROUILLON
   ----------------------------------------------------------------------------
   Le fichier HTML étant souvent ouvert depuis le téléphone en `file://`,
   le navigateur peut refuser tout stockage (origine opaque). On le détecte au
   démarrage : si le stockage n'est pas disponible, l'application continue de
   fonctionner en mémoire et propose l'export / import d'un brouillon JSON.
   Aucune donnée n'est perdue en silence.
   ========================================================================== */

import { STORAGE_KEY } from '../config';
import type { AuditData } from '../schema/types';

export type StorageState = 'ok' | 'indisponible';

let etat: StorageState = 'indisponible';

/** Teste réellement l'écriture — `typeof localStorage` ne suffit pas :
 *  en `file://` l'objet existe mais lève une exception à l'écriture. */
export function initStorage(): StorageState {
  try {
    const cle = `${STORAGE_KEY}__test`;
    window.localStorage.setItem(cle, '1');
    window.localStorage.removeItem(cle);
    etat = 'ok';
  } catch {
    etat = 'indisponible';
  }
  return etat;
}

export const storageState = (): StorageState => etat;

export function sauverBrouillon(data: AuditData): boolean {
  if (etat !== 'ok') return false;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
    return true;
  } catch {
    // Quota dépassé (trop de photos) : on repasse en mode sans sauvegarde
    // plutôt que de laisser croire que le brouillon est enregistré.
    etat = 'indisponible';
    return false;
  }
}

export function lireBrouillon(): AuditData | null {
  if (etat !== 'ok') return null;
  try {
    const brut = window.localStorage.getItem(STORAGE_KEY);
    return brut ? (JSON.parse(brut) as AuditData) : null;
  } catch {
    return null;
  }
}

export function effacerBrouillon(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* rien à faire */
  }
}

/** Poids approximatif du brouillon en octets (les photos base64 dominent). */
export function poidsBrouillon(data: AuditData): number {
  try {
    return new Blob([JSON.stringify(data)]).size;
  } catch {
    return 0;
  }
}

export function formaterPoids(octets: number): string {
  if (octets < 1024) return `${octets} o`;
  if (octets < 1024 * 1024) return `${Math.round(octets / 1024)} Ko`;
  return `${(octets / (1024 * 1024)).toFixed(1)} Mo`;
}

/** Télécharge le brouillon au format JSON (secours quand le stockage est
 *  indisponible, ou pour reprendre un audit sur un autre appareil). */
export function exporterBrouillon(data: AuditData, nom: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${nom}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5_000);
}

export function importerBrouillon(fichier: File): Promise<AuditData> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      try {
        resolve(JSON.parse(String(reader.result)) as AuditData);
      } catch {
        reject(new Error('Fichier illisible'));
      }
    };
    reader.onerror = () => reject(new Error('Lecture impossible'));
    reader.readAsText(fichier);
  });
}
