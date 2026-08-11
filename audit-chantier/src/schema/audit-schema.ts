/* ============================================================================
   GRILLE D'AUDIT CHANTIER QSE — D.I. ENVIRONNEMENT
   ----------------------------------------------------------------------------
   ★ C'EST LE FICHIER À MODIFIER POUR FAIRE ÉVOLUER LE FORMULAIRE. ★

   Ajouter un point de contrôle :
       ctrl('mon_id', 'Libellé du point', 'Aide affichée sous le libellé'),

   Ajouter un champ classique :
       { id: 'mon_id', type: 'text', label: 'Libellé' },

   Rendre un champ conditionnel :
       visibleIf: (a) => a.arret_travail === 'OUI',

   Ajouter un écran : copier un bloc `{ id, short, title, fields: [...] }`.

   Règle unique : `id` doit être unique et ne doit plus changer une fois
   l'application diffusée (c'est la clé de sauvegarde des brouillons).
   ========================================================================== */

import type { AuditData, ControlField, Screen } from './types';
import {
  AUDITEURS,
  CONDUCTEURS,
  FAIT_NC,
  NIVEAUX_EMPOUSSIEREMENT,
  OUI_MOE,
  OUI_NON,
  PROCESSUS_AMIANTE,
} from './options';

/** Raccourci pour un point de contrôle « Conforme / Améliorable / NA »
 *  avec commentaire, responsable, délai et photos. */
const ctrl = (
  id: string,
  label: string,
  hint?: string,
  extra: Partial<Omit<ControlField, 'id' | 'type' | 'label' | 'hint'>> = {},
): ControlField => ({ id, type: 'control', label, hint, ...extra });

/** Vrai dès qu'un processus amiante est sélectionné à l'écran 1.
 *  Pilote l'écran 6 et tous les points spécifiques désamiantage. */
export const estAmiante = (a: AuditData): boolean =>
  Array.isArray(a.processus_amiante) && a.processus_amiante.length > 0;

export const SCREENS: Screen[] = [
  /* ── ÉCRAN 1 ─────────────────────────────────────────────────────────── */
  {
    id: 'general',
    short: 'Général',
    title: 'Informations générales du site',
    intro:
      "Contexte de l'audit et intervenants. Les champs sont pré-remplis ou proposés en liste pour gagner du temps sur le terrain.",
    fields: [
      {
        id: 'date_audit',
        type: 'datetime',
        label: "Date et heure de l'audit",
        hint: "Renseignée automatiquement à l'ouverture.",
        required: true,
      },
      {
        id: 'chantier',
        type: 'text',
        label: 'Nom et nature du chantier',
        hint: 'Ex. : Diag à la pelle.',
        placeholder: 'Ex. : Diag à la pelle',
        required: true,
      },
      {
        id: 'lieu',
        type: 'geoloc',
        label: 'Lieu / Site',
        hint: 'Saisie libre, ou relevé GPS automatique.',
        required: true,
      },
      {
        id: 'auditeur',
        type: 'select',
        label: "Auditeur / Auteur de la visite",
        options: AUDITEURS,
        allowOther: true,
        required: true,
      },
      {
        id: 'conducteur',
        type: 'select',
        label: 'Conducteur de travaux / Responsable',
        options: CONDUCTEURS,
        allowOther: true,
        required: true,
      },
      {
        id: 'personnels',
        type: 'textarea',
        label: 'Personnels DIER et sous-traitants présents',
        hint: 'Personnes présentes sur le site et typologie (intérimaires, sous-traitants…).',
        rows: 3,
      },
      {
        id: 'arret_travail',
        type: 'radio',
        label: "Arrêt exigé du travail pendant la visite",
        options: OUI_NON,
        inline: true,
        required: true,
      },
      {
        id: 'reprise_meme_jour',
        type: 'radio',
        label: 'Reprise le même jour',
        options: OUI_NON,
        inline: true,
        required: true,
        visibleIf: (a) => a.arret_travail === 'OUI',
      },
      {
        id: 'travaux_en_cours',
        type: 'radio',
        label: 'Travaux en cours',
        options: OUI_MOE,
        inline: true,
        required: true,
      },
      {
        id: 'processus_amiante',
        type: 'multiselect',
        label: 'Processus évalué (spécifique amiante)',
        hint: "Laisser vide si l'audit est hors amiante. Toute sélection active l'écran « Confinement et bilan aéraulique ».",
        options: PROCESSUS_AMIANTE,
        allowOther: true,
      },
      {
        id: 'empoussierement',
        type: 'radio',
        label: "Niveau d'empoussièrement",
        options: NIVEAUX_EMPOUSSIEREMENT,
        inline: true,
        required: true,
        visibleIf: estAmiante,
      },
    ],
  },

  /* ── ÉCRAN 2 ─────────────────────────────────────────────────────────── */
  {
    id: 'organisation',
    short: 'Organisation',
    title: 'Situation générale, procédures et organisation',
    ref: 'A & B',
    intro:
      "Conformité documentaire, affichages réglementaires obligatoires et organisation générale du chantier.",
    fields: [
      ctrl(
        'visiteurs_accueil',
        'Enregistrement des visiteurs et accueil sécurité',
        'Photo du registre. Commenter si manquant.',
        { photoRequise: true },
      ),
      ctrl('securite_cloture', 'Sécurité générale / clôture', "Photo de l'état de la clôture.", {
        photoRequise: true,
      }),
      ctrl(
        'plan_securite',
        'Plan sécurité disponible et à jour (PDRE, PP, PPSPS)',
        'Documentation H&S établie, adaptée et signée.',
      ),
      ctrl(
        'procedures_fiches',
        "Procédures comprises, respectées et fiches d'instructions",
        'Observation terrain.',
      ),
      ctrl(
        'coactivite',
        'Gestion de la coactivité',
        'Conscience des autres activités et travailleurs présents.',
      ),
      ctrl(
        'affichages',
        'Affichages réglementaires / Logigramme accidents / Amiante',
        'Photo des affichages obligatoire.',
        { photoRequise: true },
      ),
      ctrl(
        'protocoles_securite',
        'Protocoles de sécurité (chargement / déchargement, levage)',
        "Vérifier l'examen d'adéquation en cas de levage.",
      ),
      ctrl('fds', 'Fiches de Données de Sécurité (FDS)', 'Disponibilité vérifiée.'),
      ctrl(
        'developpement_durable',
        'Démarche Développement Durable',
        'Pratiques spécifiques au projet (zonage des enjeux écologiques…).',
      ),
    ],
  },

  /* ── ÉCRAN 3 ─────────────────────────────────────────────────────────── */
  {
    id: 'hygiene',
    short: 'Hygiène',
    title: 'Hygiène, santé et base vie',
    ref: 'C',
    intro: "Installations pour le bien-être et la santé du personnel sur le chantier.",
    fields: [
      ctrl('trousse_secours', 'Trousse de secours', 'Vérifier inventaire et matériel périmé.'),
      ctrl(
        'point_eau',
        "Point d'eau — Lavabo",
        'Ex. : emprunter les sanitaires voisins si besoin.',
      ),
      ctrl(
        'toilettes_restauration',
        'Toilettes et zone dédiée à la restauration',
        'Propreté et disponibilité.',
      ),
      ctrl(
        'proprete_sas',
        'Propreté des SAS (hygiène et personnel)',
        "Spécifique amiante. Photo obligatoire (ex. : absence de scotch…).",
        { photoRequise: true, visibleIf: estAmiante },
      ),
    ],
  },

  /* ── ÉCRAN 4 ─────────────────────────────────────────────────────────── */
  {
    id: 'risques',
    short: 'Risques',
    title: 'Identification des risques sur le terrain',
    ref: 'D',
    intro:
      "Risques physiques, chimiques, environnementaux et comportementaux observés pendant la visite.",
    fields: [
      ctrl(
        'trebuchement',
        'Trébuchement',
        'Sols inégaux, herbes hautes, obstacles. Photo des obstacles.',
        { photoRequise: true },
      ),
      ctrl(
        'chute',
        "Chute de hauteur / Chute d'objets",
        'Travail en hauteur, fouille, harnais.',
      ),
      ctrl(
        'circulation',
        'Circulation site et accès',
        'Véhicules, engins, piétons. Heurt piéton / véhicule, accès VL et VU.',
      ),
      ctrl(
        'manutention',
        'Mouvement (manutention, gestes et postures)',
        'Ex. : transport d’échantillons, port de charges (pelle, brouette).',
      ),
      ctrl(
        'mecanique',
        'Mécanique et équipement de travail',
        'Engins, outillage portatif. Utilisation conforme.',
      ),
      ctrl(
        'chimique_bio',
        'Chimique (amiante, plomb, ACD, CMR) et biologique',
        'Suivi spécifique des expositions.',
      ),
      ctrl(
        'ambiance',
        'Ambiance (bruit, thermique, lumineuse, incendie, électricité)',
        "Ex. : niveau d'exposition, machines.",
      ),
      ctrl('rps', 'Risques psychosociaux (RPS)', 'Observation du climat.'),
    ],
  },

  /* ── ÉCRAN 5 ─────────────────────────────────────────────────────────── */
  {
    id: 'environnement',
    short: 'Env. & Véhic.',
    title: 'Environnement de travail et véhicules',
    ref: 'F & G',
    intro:
      "Espace de travail direct, stockage des déchets et état des véhicules de l'entreprise.",
    fields: [
      ctrl(
        'zone_travaux',
        'Zone de travaux / circulation sans obstacle et sécurisée',
        'Systèmes de signalisation et barrières, propreté (outils, matériels).',
      ),
      ctrl(
        'epc',
        'Équipement de Protection Collective (EPC)',
        'Installation conforme.',
      ),
      ctrl(
        'stockage_dechets',
        'Stockage et enlèvement (échantillons, déchets amiante et autres)',
        'Balisage de la zone déchets, conditionnement (logo amiante), pain de glace.',
      ),
      ctrl('tracabilite', 'Traçabilité (BSD, BSDA)', 'Documents de suivi des déchets.'),
      {
        id: 'vehicule_identification',
        type: 'text',
        label: 'Véhicule — Type et immatriculation',
        hint: 'Ex. : Renault Master — AB-123-CD',
        placeholder: 'Type — Immatriculation',
      },
      ctrl(
        'vehicule_etat',
        'Véhicule — État général',
        'Contrôle technique à jour, absence d’anomalie. Photo si anomalie.',
      ),
      ctrl(
        'vehicule_equipement',
        'Véhicule — Trousse de secours, gilet jaune, triangle',
        'Présence à portée de main, matériel non périmé.',
      ),
    ],
  },

  /* ── ÉCRAN 6 (amiante) ───────────────────────────────────────────────── */
  {
    id: 'aeraulique',
    short: 'Aéraulique',
    title: 'Confinement et bilan aéraulique',
    ref: 'Spécifique amiante — NF X 46-010',
    intro:
      "Cet écran n'apparaît que si un processus amiante est sélectionné à l'écran 1.",
    visibleIf: estAmiante,
    fields: [
      {
        id: 'vitesse_air_sas',
        type: 'number',
        label: "Vitesse d'air dans les SAS (porte ouverte)",
        unit: 'm/s',
        step: 0.01,
        min: 0,
        required: true,
        hint: 'Seuil réglementaire : 0,5 m/s.',
        alert: (v) =>
          v < 0.5
            ? "ALERTE — Vitesse inférieure à 0,5 m/s. Action corrective et validation obligatoires."
            : null,
      },
      {
        id: 'depression_zone',
        type: 'number',
        label: 'Dépression de la zone de travail',
        unit: 'Pa',
        step: 1,
        min: 0,
        required: true,
        hint: 'Seuil réglementaire : 10 Pa.',
        alert: (v) =>
          v < 10
            ? 'ALERTE — Dépression inférieure à 10 Pa. Action corrective et validation obligatoires.'
            : null,
      },
      {
        id: 'test_fumee_realise',
        type: 'checkbox',
        label: 'Test de fumée réalisé (étanchéité et zones mortes)',
        required: true,
      },
      {
        id: 'test_fumee_media',
        type: 'media',
        label: 'Test de fumée — photo ou vidéo',
        hint: 'Vidéo de 15 secondes maximum, ou photo. Obligatoire.',
        video: true,
        maxSeconds: 15,
        multiple: true,
        required: true,
        visibleIf: (a) => a.test_fumee_realise === true,
      },
      {
        id: 'groupe_electrogene',
        type: 'radio',
        label: 'Matériel — Test groupe électrogène / extracteur de secours',
        options: FAIT_NC,
        inline: true,
        required: true,
      },
      {
        id: 'journal_electrique',
        type: 'media',
        label: 'Photo du journal journalier électrique / tableau',
        multiple: true,
      },
    ],
  },

  /* ── ÉCRAN 7 ─────────────────────────────────────────────────────────── */
  {
    id: 'cloture',
    short: 'Clôture',
    title: 'Clôture, commentaires globaux et signatures',
    intro:
      "Bilan de la visite, validation des intervenants et déclenchement du flux d'information.",
    fields: [
      {
        id: 'commentaires_globaux',
        type: 'textarea',
        label: 'Commentaires globaux',
        hint: "Ressenti général (ex. : « Chantier maîtrisé malgré le contexte d'intervention… »).",
        rows: 5,
      },
      {
        id: 'actions_immediates',
        type: 'textarea',
        label: 'Actions correctives immédiates',
        hint: "Ce qui a été corrigé pendant l'audit.",
        rows: 4,
      },
      {
        id: 'signature_auditeur',
        type: 'signature',
        label: 'Signature auditeur',
        hint: 'Obligatoire.',
        required: true,
      },
      {
        id: 'signature_responsable',
        type: 'signature',
        label: 'Signature chef de chantier / responsable',
        hint: 'Vaut acceptation des constats.',
        required: true,
      },
    ],
  },
];
