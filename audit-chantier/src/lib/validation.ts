/* ============================================================================
   VISIBILITÉ, COMPLÉTUDE ET RÈGLES MÉTIER
   ----------------------------------------------------------------------------
   Toute la logique dérive du schéma : ajouter un champ dans `audit-schema.ts`
   le fait automatiquement entrer dans le calcul de progression, de validation
   et dans le rapport PDF.
   ========================================================================== */

import { SCREENS } from '../schema/audit-schema';
import type {
  AuditData,
  ControlValue,
  Field,
  Media,
  NumberField,
  Screen,
} from '../schema/types';

export const ecransVisibles = (a: AuditData): Screen[] =>
  SCREENS.filter((e) => !e.visibleIf || e.visibleIf(a));

export const champsVisibles = (ecran: Screen, a: AuditData): Field[] =>
  ecran.fields.filter((f) => !f.visibleIf || f.visibleIf(a));

export const estControl = (v: unknown): v is ControlValue =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

/** Un champ est-il renseigné ? */
export function estRempli(champ: Field, valeur: unknown): boolean {
  if (champ.type === 'control') {
    return estControl(valeur) && !!valeur.evaluation;
  }
  if (champ.type === 'checkbox') return valeur === true;
  if (champ.type === 'media') return Array.isArray(valeur) && valeur.length > 0;
  if (champ.type === 'multiselect') return Array.isArray(valeur) && valeur.length > 0;
  if (champ.type === 'number') return typeof valeur === 'number' && !Number.isNaN(valeur);
  return typeof valeur === 'string' ? valeur.trim() !== '' : valeur != null;
}

export interface Anomalie {
  ecranId: string;
  ecranTitre: string;
  champId: string;
  champLabel: string;
  message: string;
  /** `bloquant` empêche la clôture de l'audit. */
  niveau: 'bloquant' | 'alerte';
}

/** Champs obligatoires non renseignés + alertes métier déclenchées. */
export function anomalies(a: AuditData): Anomalie[] {
  const liste: Anomalie[] = [];

  for (const ecran of ecransVisibles(a)) {
    for (const champ of champsVisibles(ecran, a)) {
      const valeur = a[champ.id];

      if (champ.required && !estRempli(champ, valeur)) {
        liste.push({
          ecranId: ecran.id,
          ecranTitre: ecran.title,
          champId: champ.id,
          champLabel: champ.label,
          message: 'Champ obligatoire non renseigné',
          niveau: 'bloquant',
        });
      }

      // Une photo annoncée comme obligatoire dans le cahier des charges n'est
      // exigée que si le point est effectivement évalué (hors « non applicable »).
      if (champ.type === 'control' && champ.photoRequise && estControl(valeur)) {
        const medias = (valeur.medias ?? []) as Media[];
        if (valeur.evaluation && valeur.evaluation !== 'NA' && medias.length === 0) {
          liste.push({
            ecranId: ecran.id,
            ecranTitre: ecran.title,
            champId: champ.id,
            champLabel: champ.label,
            message: 'Photo attendue sur ce point de contrôle',
            niveau: 'alerte',
          });
        }
      }

      if (champ.type === 'number' && typeof valeur === 'number') {
        const message = (champ as NumberField).alert?.(valeur);
        if (message) {
          liste.push({
            ecranId: ecran.id,
            ecranTitre: ecran.title,
            champId: champ.id,
            champLabel: champ.label,
            message,
            niveau: 'bloquant',
          });
        }
      }
    }
  }

  return liste;
}

/** Points de contrôle évalués « Améliorable » — le cœur du rapport. */
export function nonConformites(a: AuditData) {
  const liste: {
    ecran: string;
    ref?: string;
    label: string;
    commentaire: string;
    responsable: string;
    delai: string;
  }[] = [];

  for (const ecran of ecransVisibles(a)) {
    for (const champ of champsVisibles(ecran, a)) {
      if (champ.type !== 'control') continue;
      const v = a[champ.id];
      if (estControl(v) && v.evaluation === 'A') {
        liste.push({
          ecran: ecran.title,
          ref: ecran.ref,
          label: champ.label,
          commentaire: v.commentaire?.trim() || '—',
          responsable: v.responsable?.trim() || '—',
          delai: v.delai?.trim() || '—',
        });
      }
    }
  }
  return liste;
}

/** Progression 0–100 sur l'ensemble des champs visibles. */
export function progression(a: AuditData): number {
  let total = 0;
  let faits = 0;
  for (const ecran of ecransVisibles(a)) {
    for (const champ of champsVisibles(ecran, a)) {
      total += 1;
      if (estRempli(champ, a[champ.id])) faits += 1;
    }
  }
  return total === 0 ? 0 : Math.round((faits / total) * 100);
}

/** Progression d'un écran donné — alimente la pastille de navigation. */
export function progressionEcran(ecran: Screen, a: AuditData): number {
  const champs = champsVisibles(ecran, a);
  if (champs.length === 0) return 100;
  const faits = champs.filter((c) => estRempli(c, a[c.id])).length;
  return Math.round((faits / champs.length) * 100);
}

/** Compteurs C / A / NA pour la synthèse. */
export function bilan(a: AuditData) {
  let C = 0;
  let A = 0;
  let NA = 0;
  for (const ecran of ecransVisibles(a)) {
    for (const champ of champsVisibles(ecran, a)) {
      if (champ.type !== 'control') continue;
      const v = a[champ.id];
      if (!estControl(v)) continue;
      if (v.evaluation === 'C') C += 1;
      else if (v.evaluation === 'A') A += 1;
      else if (v.evaluation === 'NA') NA += 1;
    }
  }
  return { C, A, NA, evalues: C + A + NA };
}
