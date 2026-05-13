/**
 * voz/js/auth.js — Gestión del Bearer token en localStorage.
 *
 * El token JWT lo emite Angel desde el VPS:
 *   python3 /home/nosvers/voz/scripts/issue_token.py --device movil-angel
 * y lo pega manualmente en la PWA (formulario onboarding).
 *
 * Se revoca con:
 *   python3 /home/nosvers/voz/scripts/revoke_token.py --jti <jti>
 */

const KEY_TOKEN  = 'nosvers_voz_token';
const KEY_DEVICE = 'nosvers_voz_device';

export function setToken(token, deviceLabel) {
  if (!token) return;
  localStorage.setItem(KEY_TOKEN, token.trim());
  if (deviceLabel) localStorage.setItem(KEY_DEVICE, deviceLabel);
}

export function getToken() {
  return localStorage.getItem(KEY_TOKEN) || '';
}

export function getDeviceLabel() {
  return localStorage.getItem(KEY_DEVICE) || 'movil-angel';
}

export function setDeviceLabel(deviceLabel) {
  if (!deviceLabel) return;
  localStorage.setItem(KEY_DEVICE, deviceLabel);
}

export function hasDeviceLabel() {
  return !!localStorage.getItem(KEY_DEVICE);
}

export function clearToken() {
  localStorage.removeItem(KEY_TOKEN);
}

export function hasToken() {
  return !!getToken();
}

/**
 * Decodifica el payload del JWT sin verificar firma — sólo para mostrar
 * device_label/exp en UI. La verificación real la hace el servidor.
 */
export function decodePayload(token) {
  try {
    const parts = token.split('.');
    if (parts.length < 2) return null;
    // base64url → base64
    let b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    while (b64.length % 4) b64 += '=';
    const json = atob(b64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}
