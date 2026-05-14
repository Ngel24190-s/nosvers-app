// Fetch wrapper: añade Authorization Bearer y X-Claudio-Context.

import { getToken, clearToken, type Context } from './auth';

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, code: string | undefined, msg: string) {
    super(msg);
    this.status = status;
    this.code = code;
  }
}

export async function apiFetch(
  path: string,
  opts: RequestInit & { context?: Context | null } = {}
): Promise<Response> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (opts.context) headers['X-Claudio-Context'] = opts.context;
  if (
    opts.body &&
    !(opts.body instanceof FormData) &&
    !(opts.body instanceof Blob) &&
    !headers['Content-Type']
  ) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(path, { ...opts, headers });
  if (res.status === 401) {
    clearToken();
  }
  return res;
}

export async function apiJson<T = unknown>(
  path: string,
  opts: RequestInit & { context?: Context | null } = {}
): Promise<T> {
  const res = await apiFetch(path, opts);
  let data: any = {};
  try {
    data = await res.json();
  } catch {
    /* empty body */
  }
  if (!res.ok) {
    throw new ApiError(res.status, data?.error, data?.detalle ?? res.statusText);
  }
  return data as T;
}
