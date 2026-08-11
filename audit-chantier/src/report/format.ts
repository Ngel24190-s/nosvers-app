/* Mise en forme des valeurs pour le rapport et l'e-mail. */

import type { AuditData, ChoiceField, Field, Media, NumberField } from '../schema/types';

export function formaterDate(iso: string | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formaterJour(iso: string | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString('fr-FR');
}

const libelle = (champ: ChoiceField, v: string) =>
  champ.options.find((o) => o.value === v)?.label ?? v;

/** Représentation texte d'un champ simple (hors `control` et `signature`). */
export function valeurTexte(champ: Field, data: AuditData): string {
  const v = data[champ.id];
  if (v === undefined || v === null || v === '') return '—';

  switch (champ.type) {
    case 'datetime':
      return formaterDate(v as string);
    case 'checkbox':
      return v === true ? 'Oui' : 'Non';
    case 'number': {
      const unit = (champ as NumberField).unit;
      return `${String(v).replace('.', ',')}${unit ? ` ${unit}` : ''}`;
    }
    case 'select':
    case 'radio':
      return libelle(champ as ChoiceField, String(v)).trim() || '—';
    case 'multiselect': {
      const arr = v as string[];
      if (!arr.length) return '—';
      return arr.map((x) => libelle(champ as ChoiceField, x)).join(' · ');
    }
    case 'media': {
      const medias = v as Media[];
      return medias.length ? `${medias.length} pièce(s) jointe(s)` : '—';
    }
    default:
      return String(v).trim() || '—';
  }
}

/** Nom de fichier sûr : pas d'accent ni de caractère interdit. */
export function nomFichier(data: AuditData): string {
  const chantier = String(data.chantier ?? 'chantier')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 40);
  const d = new Date(String(data.date_audit ?? Date.now()));
  const jour = Number.isNaN(d.getTime())
    ? 'sans-date'
    : `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
  return `Audit-QSE_${chantier || 'chantier'}_${jour}`;
}
