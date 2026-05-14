// Auth helpers (007) — JWT en localStorage, decode sin verificar firma.
// Cliente confía en backend para validación; aquí solo necesita conocer
// `sub` y `available_contexts` para mostrar la UI correcta.

const TOKEN_KEY = 'claudio.token';

export type Context = 'casa' | 'nosvers' | 'trabajo';

export interface JwtPayload {
  jti?: string;
  sub?: string;
  device?: string;
  iat?: number;
  exp?: number;
  available_contexts?: Context[];
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

function b64urlDecode(s: string): string {
  s = s.replace(/-/g, '+').replace(/_/g, '/');
  while (s.length % 4) s += '=';
  try {
    return decodeURIComponent(
      atob(s)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
  } catch {
    return atob(s);
  }
}

export function decodeJwt(token: string | null): JwtPayload | null {
  if (!token) return null;
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(b64urlDecode(parts[1])) as JwtPayload;
  } catch {
    return null;
  }
}

export function getAvailableContexts(): Context[] {
  const p = decodeJwt(getToken());
  return (p?.available_contexts as Context[] | undefined) ?? ['casa', 'nosvers'];
}

export function getSub(): string {
  const p = decodeJwt(getToken());
  return p?.sub ?? 'angel';
}

export function isExpired(): boolean {
  const p = decodeJwt(getToken());
  if (!p?.exp) return true;
  return Date.now() / 1000 >= p.exp;
}
