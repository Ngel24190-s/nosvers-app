# Data Model — Asistente de Voz Personal NosVers

**Feature**: 001-voice-assistant
**Date**: 2026-05-12 (actualizado 2026-05-13 por addendum BRIEF §14)

Todas las entidades persisten como markdown en el vault NosVers
(`/home/nosvers/public_html/knowledge_base/`, **pool común multi-usuario**)
salvo la cola IndexedDB que vive en el cliente PWA.

> **⚠ Addendum multi-usuario (BRIEF §14, 2026-05-13)**
> - Cada entidad `Nota` añade el campo `autor: "angel" | "africa"`.
> - Path base ya no incluye `/angel/`. El segmento por usuario desaparece.
> - Audio: nombre `HH-MM-SS_{autor}.opus`.
> - Nueva entidad `Speaker` (embedding 256-d) en
>   `system/speakers/{autor}.npy`.
> - Nuevo campo en JWT auth: `sub: "angel" | "africa"` (= autor del token).

---

## 1. Archivo del día (`dia/YYYY-MM-DD.md`)

Cronología de notas de un día. Verdad permanente.

**Path**: `knowledge_base/angel/dia/2026-05-12.md`

**Esquema**: Markdown con un bloque por nota. Cada nota lleva frontmatter
YAML embebido en una valla `---` para parsing fiable. Formato:

```markdown
# Diario — 2026-05-12

---
ts: 2026-05-12T09:23:45+02:00
etiqueta: nosvers
origen: voz_movil
audio: audio/2026-05-12/09-23-45.opus
clasificador_confianza: 0.92
clasificador_modelo: claude-haiku-4-5
---

Pedir a África las fotos del extracto vivo antes del viernes — necesito
3 verticales para el carrusel.

---
ts: 2026-05-12T14:10:02+02:00
etiqueta: trabajo
origen: voz_linux
audio: null
clasificador_confianza: 0.88
clasificador_modelo: claude-haiku-4-5
---

Reunión con el chef de obra de Bordeaux mañana 09:00. Llevar el plan de
desamiantage actualizado y dosímetros.

```

**Campos del frontmatter por nota**:

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `ts` | ISO 8601 con tz | Sí | Timestamp del momento de dictado, no de sync. |
| `etiqueta` | enum | Sí | `trabajo` \| `nosvers` \| `familia` \| `mental` \| `idea` \| `otro` |
| `origen` | enum | Sí | `voz_movil` \| `voz_linux` \| `texto_directo` \| `otro` |
| `audio` | string\|null | Sí | Path relativo al vault, o `null` si nunca hubo audio o ya fue purgado. |
| `clasificador_confianza` | float [0..1] | Sí | Si fallback `otro`, valor `0.0`. |
| `clasificador_modelo` | string | Sí | Modelo concreto usado, o `fallback` si se etiquetó por fallback. |

**Reglas**:
- Si `etiqueta` es `otro` y `clasificador_confianza` es `0.0`, la nota es
  candidata a reclasificación en el siguiente ciclo de `agt07_diario`.
- El archivo se crea si no existe. Las notas se appendean en orden
  cronológico por `ts`. Si llegan desordenadas (sync diferido de la PWA),
  el archivo se reordena por `ts` antes de escribirse.
- Cabecera `# Diario — YYYY-MM-DD` se preserva.

---

## 2. Audio efímero (`dia/audio/YYYY-MM-DD/HH-MM-SS.opus`)

**Path**: `knowledge_base/angel/dia/audio/2026-05-12/09-23-45.opus`

**Formato**: Opus codec en contenedor `.opus` (no `.ogg`), bitrate
24 kbps mono — ~30 KB/min.

**Reglas**:
- Nombre = `HH-MM-SS.opus` (timestamp local de captura).
- Subcarpetas por día (`YYYY-MM-DD/`) para facilitar la purga: cron borra
  subcarpetas enteras cuya fecha del nombre es > 7 días.
- TTL estricto: nunca persiste más de 7 días en el VPS (SC-012).

---

## 3. Resumen del día (`dia/resumenes/YYYY-MM-DD.md`)

Generado por `agt07_diario` cada noche a las 23:30.

**Path**: `knowledge_base/angel/dia/resumenes/2026-05-12.md`

**Esquema**:

```markdown
---
fecha: 2026-05-12
tipo: dia
notas_procesadas: 7
modelo: claude-haiku-4-5
generado_ts: 2026-05-12T23:30:14+02:00
---

# Resumen del 2026-05-12

## Síntesis

Día centrado en obra (Bordeaux) y arranque del carrusel Instagram para
NosVers. Pendiente clave: fotos del extracto vivo que África debe enviar
antes del viernes. Una idea suelta sobre formato de PDF Club mensual sin
desarrollar aún.

## Ideas y pendientes

- [ ] Pedir fotos extracto vivo a África (deadline viernes)
- [ ] Plan desamiantage Bordeaux — revisar dosímetros mañana 09:00
- [ ] Idea: PDF Club mes 1 podría enfocarse en "primer suelo vivo"

## Distribución de etiquetas

```
trabajo:   ▓▓▓▓▓ 5
nosvers:   ▓▓ 2
familia:   ▓ 1
idea:      ▓ 1
mental:    0
otro:      0
```
```

**Reglas**:
- Si `notas_procesadas == 0`, el archivo NO se crea (FR-022).
- El bloque de ideas/pendientes usa checkboxes `- [ ]` para que sean
  marcables en Obsidian.
- El gráfico de etiquetas usa `▓` repetido = cantidad. Fácil de leer en
  texto plano o markdown rendering.

---

## 4. Resumen semanal (`dia/resumenes/YYYY-Www.md`)

Generado por `agt07_diario` cada domingo a las 22:00.

**Path**: `knowledge_base/angel/dia/resumenes/2026-W19.md` (ISO week number).

**Esquema**: similar al diario pero con secciones extra:

```markdown
---
fecha_inicio: 2026-05-05
fecha_fin: 2026-05-12
semana_iso: 2026-W19
tipo: semana
dias_con_actividad: 6
notas_totales: 38
modelo: claude-opus-4-7
generado_ts: 2026-05-12T22:00:42+02:00
---

# Resumen semana 2026-W19 (lun 5 → dom 12 mayo)

## Hilos principales
…

## Tendencias detectadas
…

## Pendientes recurrentes (no cerrados esta semana)
…

## Distribución de etiquetas (acumulada)
…

## Comparación con semana anterior
…
```

---

## 5. Prompt de clasificación (`prompts/clasificar_nota.md`)

Editable a mano por Angel sin redespliegue.

**Path**: `knowledge_base/angel/prompts/clasificar_nota.md`

**Esquema**:

```markdown
---
nombre: clasificar_nota
modelo: claude-haiku-4-5
version: 1
---

# Prompt: clasificar nota dictada

Eres un clasificador. Recibes una nota corta dictada por Angel.
Devuelve EXCLUSIVAMENTE un JSON con tres campos:
{"etiqueta": "<una de: trabajo|nosvers|familia|mental|idea|otro>",
 "confianza": <float 0..1>,
 "razon": "<máx 12 palabras explicando la elección>"}

Reglas:
- "trabajo" = DI Environnement, desamiantage, obra, dosímetros, chef de obra.
- "nosvers" = ferme, vermicultura, lombricompost, África, club, WordPress, Instagram NosVers.
- "familia" = hijos, África en plano personal, casa, escuela.
- "mental" = pensamiento personal, estado de ánimo, reflexión.
- "idea" = chispazo, hipótesis nueva, formato a explorar.
- "otro" = no encaja claro en las anteriores.

Si la nota es ambigua entre dos, devuelve la más probable y baja la confianza.
```

---

## 6. Cola IndexedDB de la PWA

Vive en el navegador del móvil de Angel, no en el VPS.

**Database**: `nosvers-voz`
**Object Store**: `notas_pendientes`
**KeyPath**: `id` (UUID v4)

**Schema del registro**:

```json
{
  "id": "uuid-v4",
  "ts_captura": "2026-05-12T09:23:45+02:00",
  "ts_intento_ultimo": null,
  "intentos": 0,
  "estado": "pendiente",
  "audio_blob": "<Blob Opus>",
  "tamaño_bytes": 84320,
  "transcript_local": null,
  "etiqueta_sugerida": null,
  "device_id": "movil-angel"
}
```

**Estados posibles**: `pendiente` | `subiendo` | `enviado` | `fallido_reintento`.

**Reglas**:
- `intentos` se incrementa en cada intento de sync; max 5 → estado `fallido_reintento`
  y notificación al usuario en la UI.
- Tras `enviado`, el registro se borra de IndexedDB (no se acumula
  histórico). El servidor es la verdad.
- Espejo del TTL del servidor: cualquier registro con `ts_captura` > 7
  días se purga del IndexedDB al abrir la app (función de housekeeping).

---

## 7. Tabla de tokens revocables (SQLite VPS)

**Path**: `/home/nosvers/voz/data/tokens.sqlite`

**Schema**:

```sql
CREATE TABLE tokens (
    jti           TEXT PRIMARY KEY,
    device_label  TEXT NOT NULL,
    issued_at     TEXT NOT NULL,
    expires_at    TEXT NOT NULL,
    revoked_at    TEXT
);

CREATE INDEX idx_tokens_revoked ON tokens(revoked_at);
```

**Reglas**:
- Cada `jti` es un UUID v4.
- Validación en cada request: si `revoked_at IS NOT NULL` → 401.
- Esta tabla es la única excepción "estado en SQL" permitida; está justificada
  por constitution III: cache de control no es contenido de usuario.

---

## 8. Estado de sesión voz (Linux client, in-memory)

No persiste a disco. Estructura interna del daemon `nosvers_voz`:

```python
@dataclass
class SesionVoz:
    activa: bool
    iniciada_ts: datetime | None
    idioma_actual: str  # "es" | "fr"
    velocidad_tts: float  # 0.5..2.0
    contexto_conversacion: list[dict]  # mensajes para la API Claude
    ultimo_input_ts: datetime | None
    cooldown_wake_hasta: datetime | None
```

**Transiciones**:
- `IDLE → DESPIERTA` por wake word detectado.
- `DESPIERTA → ACTIVA` tras primer input del usuario.
- `ACTIVA → IDLE` por timeout 8s sin habla nueva o por "cierra sesión".
- `* → IDLE` si timeout 5min total de sesión.

---

## Relaciones

```
Nota dictada ──persiste en──> Archivo del día
Nota dictada ──puede tener──> Audio efímero (TTL 7d)
Archivo del día ──input a──> agt07_diario ──genera──> Resumen del día
7×Archivo del día ──input a──> agt07_diario ──genera──> Resumen semanal
PWA ──auth con──> Token revocable
PWA ──encola en──> IndexedDB ──sync a──> dia_capturar ──persiste──> Archivo del día
Linux client ──invoca──> Tools MCP (dia_*, vault_*, etc.)
```
