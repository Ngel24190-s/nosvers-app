/* ============================================================================
   CONFIGURATION — à ajuster sans toucher au reste du code
   ========================================================================== */

/** Destinataire par défaut du rapport d'audit (service QSE). */
export const EMAIL_QSE = 'qse@di-environnement.fr';

/** En copie (laisser vide si inutile). */
export const EMAIL_CC = '';

/** Nom de l'entité affiché dans l'en-tête de l'application et du PDF. */
export const ENTITE = 'D.I. ENVIRONNEMENT';
export const AGENCE = 'Sud-Ouest';

/** Version affichée en pied de page — à incrémenter à chaque diffusion. */
export const VERSION = '1.0';

/** Compression des photos avant stockage (le fichier doit rester léger). */
export const PHOTO_MAX_PX = 1280;
export const PHOTO_QUALITY = 0.7;

/** Seuil d'alerte sur le poids total du brouillon (octets). */
export const POIDS_ALERTE = 4 * 1024 * 1024;

/** Clé de sauvegarde locale du brouillon. */
export const STORAGE_KEY = 'dier-audit-chantier-v1';
