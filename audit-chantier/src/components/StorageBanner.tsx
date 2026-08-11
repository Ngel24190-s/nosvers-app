import { POIDS_ALERTE } from '../config';
import { formaterPoids } from '../storage/storage';
import type { StorageState } from '../storage/storage';

export function StorageBanner({ etat, poids }: { etat: StorageState; poids: number }) {
  if (etat === 'indisponible') {
    return (
      <p className="no-print border-b-2 border-di bg-di-light px-4 py-2 text-[12px] leading-snug text-di-dark">
        <strong className="uppercase tracking-di">Mode sans sauvegarde.</strong> Ce navigateur
        n'autorise pas l'enregistrement local — terminez l'audit en une fois, ou exportez le
        brouillon depuis l'écran Clôture.
      </p>
    );
  }
  if (poids > POIDS_ALERTE) {
    return (
      <p className="no-print border-b-2 border-di bg-di-light px-4 py-2 text-[12px] text-di-dark">
        Brouillon volumineux ({formaterPoids(poids)}) — clôturez l'audit pour libérer la mémoire.
      </p>
    );
  }
  return null;
}
