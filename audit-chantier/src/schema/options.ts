/* ============================================================================
   LISTES DÉROULANTES — le fichier qui bouge le plus souvent
   ----------------------------------------------------------------------------
   Ajouter / retirer une personne = ajouter / retirer une ligne. Rien d'autre.
   ========================================================================== */

import type { Option } from './types';

const opt = (label: string): Option => ({ value: label, label });

/** Auditeurs / auteurs de la visite. */
export const AUDITEURS: readonly Option[] = [
  'Denis DEL AGUILA',
  'Nadia BOURAGHDA',
  'Dorian DANET',
].map(opt);

/** Conducteurs de travaux / responsables de chantier. */
export const CONDUCTEURS: readonly Option[] = [
  'Angel BAEZA',
  'Michel GALZIN',
].map(opt);

/** Processus amiante évalués. Sélectionner au moins un processus fait
 *  apparaître l'écran 6 (Confinement et bilan aéraulique) et les points de
 *  contrôle spécifiques amiante. */
export const PROCESSUS_AMIANTE: readonly Option[] = [
  { value: '18-14-M1', label: '18-14-M1 — Retrait joint sur gaine' },
];

/** Niveaux d'empoussièrement réglementaires. */
export const NIVEAUX_EMPOUSSIEREMENT: readonly Option[] = [
  { value: 'N1', label: 'Niveau 1' },
  { value: 'N2', label: 'Niveau 2' },
  { value: 'N3', label: 'Niveau 3' },
];

export const OUI_NON: readonly Option[] = [
  { value: 'OUI', label: 'OUI' },
  { value: 'NON', label: 'NON' },
];

export const OUI_MOE: readonly Option[] = [
  { value: 'OUI', label: 'OUI' },
  { value: 'MOE', label: 'MOE' },
];

export const FAIT_NC: readonly Option[] = [
  { value: 'FAIT', label: 'Fait' },
  { value: 'NC', label: 'Non conforme' },
  { value: 'NA', label: 'Non applicable' },
];
