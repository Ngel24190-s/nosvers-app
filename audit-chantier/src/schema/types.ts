/* ============================================================================
   CONTRAT DU FORMULAIRE
   ----------------------------------------------------------------------------
   Ce fichier décrit *ce qu'un champ peut être*. Les champs eux-mêmes sont
   déclarés dans `audit-schema.ts`. Pour ajouter un point de contrôle, il n'y a
   normalement rien à modifier ici.
   ========================================================================== */

/** Évaluation d'un point de contrôle. */
export type Evaluation = 'C' | 'A' | 'NA';

export const EVALUATIONS: { value: Evaluation; label: string; short: string }[] = [
  { value: 'C', label: 'Conforme', short: 'C' },
  { value: 'A', label: 'Améliorable', short: 'A' },
  { value: 'NA', label: 'Non applicable', short: 'NA' },
];

/** Une photo (ou une courte vidéo) stockée en base64. */
export interface Media {
  id: string;
  dataUrl: string;
  /** `image` ou `video` — détermine le rendu et l'inclusion au PDF. */
  kind: 'image' | 'video';
  name?: string;
}

/** Valeur d'un champ de type `control`. */
export interface ControlValue {
  evaluation?: Evaluation;
  commentaire?: string;
  responsable?: string;
  delai?: string;
  medias?: Media[];
}

/** L'ensemble des réponses de l'audit, indexées par `field.id`. */
export type AuditData = Record<string, unknown>;

export type FieldType =
  | 'datetime'
  | 'text'
  | 'textarea'
  | 'select'
  | 'multiselect'
  | 'radio'
  | 'number'
  | 'checkbox'
  | 'media'
  | 'geoloc'
  | 'signature'
  | 'control';

export interface Option {
  value: string;
  label: string;
}

interface FieldCommon {
  /** Identifiant unique et stable — sert de clé de stockage. Ne pas le changer
   *  une fois l'application diffusée, sous peine de perdre les brouillons. */
  id: string;
  label: string;
  /** Colonne « Comportement / Valeurs suggérées » du cahier des charges. */
  hint?: string;
  required?: boolean;
  /** Affichage conditionnel — reçoit toutes les réponses de l'audit. */
  visibleIf?: (a: AuditData) => boolean;
}

export interface TextField extends FieldCommon {
  type: 'text' | 'textarea' | 'datetime' | 'geoloc';
  placeholder?: string;
  rows?: number;
}

export interface ChoiceField extends FieldCommon {
  type: 'select' | 'multiselect' | 'radio';
  options: readonly Option[];
  /** Ajoute une entrée « Autre… » avec saisie libre. */
  allowOther?: boolean;
  /** `radio` uniquement : dispose les options en ligne (OUI / NON). */
  inline?: boolean;
}

export interface NumberField extends FieldCommon {
  type: 'number';
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
  /** Règle métier. Retourne le message d'alerte, ou `null` si la valeur passe.
   *  Une alerte non nulle bloque la validation de l'audit. */
  alert?: (v: number) => string | null;
}

export interface CheckboxField extends FieldCommon {
  type: 'checkbox';
}

export interface MediaField extends FieldCommon {
  type: 'media';
  /** Autorise la vidéo en plus de la photo (test de fumée). */
  video?: boolean;
  /** Durée maximale conseillée pour une vidéo, en secondes. */
  maxSeconds?: number;
  multiple?: boolean;
}

export interface SignatureField extends FieldCommon {
  type: 'signature';
}

export interface ControlField extends FieldCommon {
  type: 'control';
  /** Une photo est attendue sur ce point (le cahier des charges le précise). */
  photoRequise?: boolean;
}

export type Field =
  | TextField
  | ChoiceField
  | NumberField
  | CheckboxField
  | MediaField
  | SignatureField
  | ControlField;

export interface Screen {
  id: string;
  /** Titre court affiché dans la barre de navigation. */
  short: string;
  title: string;
  /** Référence de la grille DIER-QSE : (A & B), (C), (D), (F & G)… */
  ref?: string;
  intro?: string;
  visibleIf?: (a: AuditData) => boolean;
  fields: Field[];
}
