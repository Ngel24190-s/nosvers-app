# Data Model — Fase B+C

Todas las "entidades" son archivos markdown con frontmatter YAML. Ninguna se persiste en BBDD (Constitución III).

## Entidades

### 1. Nota diaria — `knowledge_base/dia/<YYYY-MM-DD>-<slug>.md`

**Estados**: `viva` ↔ `archivada` (soft delete).

```yaml
---
autor: angel | africa             # obligatorio, viene del JWT al crear
fecha: 2026-05-13                 # obligatorio (YYYY-MM-DD, TZ Europe/Madrid)
modified_at: 2026-05-13T10:42:00+02:00   # obligatorio en B+C; auto en cada write
titulo: "Idea sobre LombriThé"    # opcional; si falta → slug autogenerado
etiquetas: [idea, nosvers]        # opcional; lista de strings de la enum fija
archived_at: 2026-05-13T11:00+02:00      # solo si archivada
archive_reason: "duplicado"       # opcional
---

Cuerpo en markdown. Puede incluir `[[wiki-links]]`.
```

**Reglas de validación**:
- `autor` debe estar en `{angel, africa}` (Principio VII).
- `fecha` debe parsear como ISO date.
- `etiquetas` debe ser subconjunto de `{trabajo, nosvers, familia, mental, idea, otro}` (FR-006 — fixed enumeration en Fase A) o vacío.
- Cuerpo ≤ 1 MB (edge case spec).
- `modified_at` se actualiza en cada PATCH; el cliente lo envía en `If-Match` para concurrencia (D-003).

**Transiciones**:
- **viva → archivada**: `archived_at` se añade + archivo se mueve a `dia/archivo/`.
- **archivada → viva**: `archived_at` + `archive_reason` se eliminan + archivo vuelve a `dia/`.

### 2. Proyecto NosVers — `knowledge_base/proyectos/<slug>.md`

```yaml
---
titulo: "Tienda Lemon Squeezy"
estado: todo | doing | done | blocked    # obligatorio
modified_at: 2026-05-13T10:42:00+02:00   # obligatorio
responsable: angel | africa              # opcional
deadline: 2026-06-01                     # opcional, YYYY-MM-DD
etiquetas: [monetización]                # opcional, free-form (no enum fija)
---

Cuerpo libre con detalles del proyecto.
```

**Reglas**:
- `estado` debe estar en la enum o la tarjeta aparece en columna "sin estado" con badge warning (US6 acceptance #5).
- `responsable` en `{angel, africa, null}`.
- `deadline` debe parsear como ISO date.

**Transiciones**: cambio de `estado` por drag-and-drop (PATCH endpoint).

### 3. Wiki-link / Backlink (entidad derivada)

No tiene archivo propio. Se computa dinámicamente:

```ts
type WikiIndex = {
  byTarget: Map<slug, Array<{ source: slug; context: string }>>;
  bySource: Map<slug, Array<slug>>;
};
```

- `slug` = filename basename sin `.md`.
- `context` = ±50 caracteres alrededor del `[[link]]` en el cuerpo de la nota fuente.
- Refrescado tras `capturar` / `editar` / `archivar` / `restaurar` / `mover` (write-through, D-004).
- Notas archivadas excluidas del índice — sus links no cuentan ni a favor ni en contra.

### 4. Vault tree node (entidad derivada)

```ts
type VaultNode = {
  path: string;          // relativo a knowledge_base/
  name: string;          // basename
  type: "folder" | "file";
  children?: VaultNode[];  // solo para folders, lazy-loaded
  size?: number;           // solo para files
  modified_at?: string;    // solo para files
};
```

- Se carga lazy: `GET /vault/tree?path=<ruta>` devuelve solo los hijos directos (FR-022).

### 5. Vista activa (preferencia cliente)

`localStorage["tablero.vista"] ∈ {lista, tabla, kanban, calendario, galeria}`.

Se carga al render del Dashboard; default `lista`. Por usuario y por navegador (no se sincroniza entre dispositivos — A-006 + FR-012).

### 6. Borrador de captura (preferencia cliente)

`localStorage["tablero.draft"] = {titulo, cuerpo, etiquetas, savedAt}`.

Sobrevive cierres accidentales; se borra al guardar o descartar explícitamente (FR-003).

### 7. Estado de infra (entidad derivada)

```ts
type InfraBadge = {
  id: "vps" | "wp" | "stripe" | "aegis" | "cron" | "freqtrade";
  status: "ok" | "warn" | "error";
  value?: string | number;   // p.ej. "uptime 12d", "€42", "+1.2%"
  detail?: string;           // mensaje de error si error
  link?: string;             // URL a logs/Grafana
  last_check: string;        // ISO timestamp
};
```

Cron sub-badge incluye nested:
```ts
{ id: "cron", status: ..., crones: [
  { name: "agt05_africa", last_run: "...", expected_interval_s: 21600, status: "ok|warn|error" },
  ...
]}
```

### 8. Agente del unified-agent (catálogo en config server)

```python
AGENTS_PUBLIC = [
    {"slug": "agt05_africa", "label": "Procesar emails de África", "timeout_s": 60},
    {"slug": "agt07_diario", "label": "Briefing diario", "timeout_s": 90},
    {"slug": "agt_eisenia", "label": "Auditoría composteur", "timeout_s": 60},
    {"slug": "orchestrator", "label": "Pulse cron status", "timeout_s": 30},
]
```

Lista predefinida (no autodetectada del FS) para evitar exponer agentes internos por accidente.

### 9. Evento Google Calendar (entidad derivada)

```ts
type CalendarEvent = {
  id: string;
  summary: string;
  start: string;          // ISO datetime
  end: string;
  description?: string;
  attendees?: Array<{ email: string }>;
  hangoutLink?: string;
  htmlLink: string;       // calendar.google.com URL
  calendarId: string;     // p.ej. "primary"
};
```

### 10. Hilo Gmail (entidad derivada)

```ts
type GmailThread = {
  id: string;
  snippet: string;          // ~100 chars
  historyId: string;
  messages: Array<{
    id: string;
    from: string;
    date: string;
    subject?: string;
    body_html_sanitized?: string;   // solo en GET thread/<id>
    body_text?: string;
  }>;
};
```

## Identidad y unicidad

- **Nota**: identificada por la ruta relativa `knowledge_base/<carpeta>/<filename>.md`.
- **Proyecto**: identificado por la ruta relativa `knowledge_base/proyectos/<filename>.md`.
- **Wiki-link**: identificado por (source_slug, target_slug) — relación derivada, no almacenada.
- **Slug** (para wiki-links): `<filename>` sin extensión `.md` ni prefijo de fecha `YYYY-MM-DD-` (D-002 / D-012).

## Volúmenes esperados

- 1.000 notas vivas + ~500 archivadas tras 1 año de uso real.
- 5.000 wiki-links totales en el índice.
- 50 proyectos kanban.
- 30-50 eventos GCal próximos 7 días.
- 20-40 hilos Gmail prioritarios.

Todos estos volúmenes caben holgadamente en RAM del proceso uvicorn (~50 MB para los índices).
