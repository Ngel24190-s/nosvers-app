# Phase 1 Data Model — Second Brain Dashboard Fase A

**Date**: 2026-05-13

This document specifies the shapes the dashboard exchanges over HTTP and the validation rules enforced at the backend boundary. The vault (markdown files + frontmatter) remains the source of truth (Constitution III); no entities are persisted outside the vault.

---

## Entities

### `TimelineEntry` (response shape, not persisted)

A summary projection of a vault note suitable for list rendering.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `path` | string | derived | Vault-relative path: `dia/YYYY-MM-DD.md#<ts>` — disambiguates intra-day notes by `ts`. Used as React `key` and as the input to `/tablero/api/nota`. |
| `fecha` | string (`YYYY-MM-DD`) | filename of day file | Sort key (descending). |
| `ts` | string (ISO 8601) | frontmatter `ts` | Tie-breaker inside the day; full timestamp for "5 min ago" labels. |
| `autor` | enum (`angel` \| `africa`) | frontmatter `autor` | Normalized by `voz.vault_io._normalize_autor`. |
| `etiqueta` | enum (`trabajo` \| `nosvers` \| `familia` \| `mental` \| `idea` \| `otro`) | frontmatter `etiqueta` | Normalized; unknown → `otro`. |
| `origen` | enum (`voz_movil` \| `voz_linux` \| `texto_directo` \| `otro`) | frontmatter `origen` | Informational chip; not filterable in Fase A. |
| `titulo` | string \| null | derived | First non-empty line of body, trimmed to ≤ 120 chars, ellipsised. Null if body is empty. |
| `preview` | string | derived | First 200 chars of body, single-line (newlines→spaces), used for the list. |
| `tiene_audio` | boolean | frontmatter `audio` not null | Informational icon. |

**Notes**:
- `metadata_incompleta: boolean` is set to `true` when the frontmatter parse fell back to defaults (autor unknown, missing ts → mtime, etc.). Frontend uses it to render the FR-015 indicator.

### `NoteFull` (response shape, not persisted)

Returned by `/tablero/api/nota` for the detail view.

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Echoed back for cache/key purposes. |
| `frontmatter` | object | All parsed frontmatter keys verbatim (after normalization for the controlled fields). Rendered separately (FR-013). |
| `body_markdown` | string | Raw markdown body (post-frontmatter), unmodified. The frontend's `react-markdown` renders it. |
| `mtime` | string (ISO 8601) | Server filesystem modification time of the day file. Used by frontend as cache key + offline detection. |
| `attachments` | array of `{ src, exists, kind }` | Resolved attachment references. `exists` is `true` if the file is on disk; `kind` in `image` \| `audio` \| `other`. Lets the frontend pre-flag broken images. |

### `SearchHit` (response shape, not persisted)

Returned by `/tablero/api/buscar` — wraps a `TimelineEntry`-like core with a search snippet.

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | Same shape as `TimelineEntry.path`. |
| `fecha` | string | |
| `ts` | string | |
| `autor` | enum | |
| `etiqueta` | enum | |
| `origen` | enum | |
| `fragmento` | string | HTML fragment with `<mark>…</mark>` around the matched substring, produced by `voz.buscar._fragmento`. Frontend renders via `dangerouslySetInnerHTML` *only* after sanitization confirms `<mark>` is the only tag (or by parsing it into a React tree client-side). |

### `Identity` (response shape)

Returned by `/tablero/api/whoami` for the frontend to learn its own identity without re-decoding the JWT.

| Field | Type | Notes |
|-------|------|-------|
| `sub` | enum (`angel` \| `africa`) | From token `sub` claim. |
| `device` | string | From token `device` claim. |
| `jti` | string | From token `jti`. Useful for the frontend to log a request id correlated to the access token. |
| `exp` | integer (Unix epoch s) | Token expiry. Frontend pre-emptively redirects to login at `exp - 60 s`. |

---

## Filters & Pagination (timeline)

The `/tablero/api/timeline` endpoint accepts the following query parameters; defaults shown:

| Param | Type | Default | Validation |
|-------|------|---------|------------|
| `desde` | `YYYY-MM-DD` | `today - 30d` | Must parse as `date`; ≤ `hasta`. |
| `hasta` | `YYYY-MM-DD` | `today` | Must parse as `date`; ≥ `desde`. |
| `autor` | enum (`angel` \| `africa` \| `ambos`) | `ambos` | `ambos` means no filter; any other value not in the enum → 400. |
| `etiqueta` | enum (one of six) \| empty | empty | Empty means no filter. |
| `limit` | int | 200 | Hard cap 500 — the frontend currently never asks for more than ~120 (30 days × 4 notes/day). |
| `offset` | int | 0 | Pagination cursor. Fase A frontend does not paginate; offset is exposed for completeness. |

**Sort**: always `(fecha DESC, ts DESC)`. No client-controllable sort key.

## Error model

All endpoints return `application/json` errors with this shape:

```json
{
  "ok": false,
  "error": "string_code",
  "detalle": "human readable hint (optional)"
}
```

`error` codes used in Fase A:

| Code | HTTP | Trigger |
|------|------|---------|
| `auth_invalido` | 401 | Missing/expired/revoked JWT or bad Bearer scheme. |
| `parametro_invalido` | 400 | Bad query string (e.g., malformed date, invalid enum, `hasta < desde`). |
| `not_found` | 404 | `/tablero/api/nota` called with a `path` that does not exist or fails the safety check. |
| `path_unsafe` | 400 | `path` would resolve outside `knowledge_base/dia/` (path traversal). |
| `rate_limited` | 429 | Reserved for the application-layer rate-limit (Fase A does not enforce; nginx handles). |
| `internal_error` | 500 | Anything unhandled. Triggers the Telegram alert path via the dedup window. |

Successful responses have `ok: true` at the top level and put the payload in a domain-named field (`entradas`, `nota`, `resultados`, `identidad`) — mirroring `voz.rest` for consistency.

## Validation rules (server)

- JWT validation: `voz.auth.validar_token(token)` → must return a dict with `sub in {angel, africa}` (otherwise 401, even if signature is valid).
- Path safety for `/tablero/api/nota`: resolve `path` via `Path(VAULT_BASE / path).resolve()` and verify `resolve()` is under `(VAULT_BASE / 'dia').resolve()`. Otherwise → 400 `path_unsafe`.
- Date parsing: `date.fromisoformat`; failure → 400 `parametro_invalido` with `detalle="fecha inválida"`.
- Enum parsing: case-fold and lookup in the controlled sets (`AUTORES_VALIDOS`, `ETIQUETAS_VALIDAS`, both already exported by `voz.vault_io`).
- The `parsear_dia` function (`voz.vault_io:119`) is reused as-is for tolerant frontmatter handling — it already swallows yaml errors and continues. We rely on its existing behavior for FR-015 ("metadata corrupta").

## Relationships (informal)

```text
TimelineEntry ─────(path)─────► NoteFull
SearchHit     ─────(path)─────► NoteFull
Identity      ─────(sub)──────► (filters in TimelineEntry.autor)
```

No persistent relationships exist server-side because no DB rows are stored. The browser holds a cache (IndexedDB ring buffer of up to 30 most-recent `NoteFull` blobs keyed by `path + mtime`) for FR-016.

## State transitions

None server-side (read-only). Client-side:

- Filter state: `(desde, hasta, autor, etiqueta) → URLSearchParams → useState` — synchronized in both directions, so browser back/forward and shareable links work naturally.
- Auth state: `noLogin → loggedIn(token, sub, exp) → tokenExpiringSoon(exp - 60s, …) → loggedIn(token2) [renewal stub; Fase A simply redirects to Login] → noLogin`.
- Detail view: closed → open(`NoteFull`) → closed; Esc/back-button/swipe close it; filter state preserved across the transition (FR-017 spirit).

---

## Open data-model questions resolved during Phase 1

- **Q**: How do we identify a note uniquely if a day file holds N notes? **A**: `path = "dia/YYYY-MM-DD.md#<ts>"` — the `ts` fragment is the disambiguator. The backend parses the fragment, calls `leer_dia(date)`, finds the note with matching `ts`, returns it. If no note matches, 404.
- **Q**: Does `TimelineEntry.fecha` come from the filename or the frontmatter `ts`? **A**: Filename. The filename is the day-bucket; the `ts` further disambiguates the time-of-day. The two cannot diverge in practice because `voz.vault_io.escribir_nota` writes by date bucket. Frontend sorts on `(fecha, ts)` descending.
- **Q**: What encoding for `fragmento`? **A**: The same string `voz.buscar._fragmento` already returns — a fragment containing `<mark>…</mark>` tags. The frontend recognizes this is the only allowed tag and renders it manually rather than via `dangerouslySetInnerHTML` (sanitization belt-and-braces).
