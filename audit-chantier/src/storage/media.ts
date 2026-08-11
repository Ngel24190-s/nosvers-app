/* Compression des photos avant stockage : sans cela, quelques clichés de
   téléphone suffisent à saturer le stockage local et à rendre le PDF illisible
   par son poids. */

import { PHOTO_MAX_PX, PHOTO_QUALITY } from '../config';
import type { Media } from '../schema/types';

let compteur = 0;
const nouvelId = () => `m${Date.now().toString(36)}${(compteur++).toString(36)}`;

function lireFichier(fichier: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error('Lecture du fichier impossible'));
    reader.readAsDataURL(fichier);
  });
}

/** Redimensionne à `PHOTO_MAX_PX` sur le plus grand côté et réencode en JPEG. */
async function compresserImage(dataUrl: string): Promise<string> {
  const img = new Image();
  await new Promise<void>((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error('Image illisible'));
    img.src = dataUrl;
  });

  const echelle = Math.min(1, PHOTO_MAX_PX / Math.max(img.width, img.height));
  if (echelle === 1 && dataUrl.startsWith('data:image/jpeg')) return dataUrl;

  const canvas = document.createElement('canvas');
  canvas.width = Math.round(img.width * echelle);
  canvas.height = Math.round(img.height * echelle);
  const ctx = canvas.getContext('2d');
  if (!ctx) return dataUrl;
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', PHOTO_QUALITY);
}

/** Transforme un fichier issu de l'appareil photo en `Media` prêt à stocker. */
export async function fichierVersMedia(fichier: File): Promise<Media> {
  const estVideo = fichier.type.startsWith('video/');
  const brut = await lireFichier(fichier);
  const dataUrl = estVideo ? brut : await compresserImage(brut);
  return {
    id: nouvelId(),
    dataUrl,
    kind: estVideo ? 'video' : 'image',
    name: fichier.name,
  };
}
