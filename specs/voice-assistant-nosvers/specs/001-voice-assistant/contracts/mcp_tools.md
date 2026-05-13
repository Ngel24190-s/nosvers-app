# MCP Tools Contract — `dia_*`

**Feature**: 001-voice-assistant
**Date**: 2026-05-12 (actualizado 2026-05-13 por addendum BRIEF §14 multi-usuario)
**Server**: `nosvers-mcp-2026` (binario `/home/nosvers/mcp_server.py`)

Tres tools nuevos añadidos al servidor MCP existente. Decoradores
`@mcp.tool()` siguiendo el patrón ya implementado en `mcp_server.py`.

> **⚠ Addendum multi-usuario (BRIEF §14, 2026-05-13)**
> - Pool común: las notas ya no se segregan por usuario. Path canónico
>   `knowledge_base/dia/YYYY-MM-DD.md` (sin `/angel/`).
> - Las 3 tools ganan parámetro `autor`. En `dia_capturar` es requerido
>   (default `"angel"`); en `dia_buscar`/`dia_contexto` es opcional
>   (vacío = ambos).
> - Valores válidos: `"angel" | "africa"`.
> - Cada nota persiste su `autor` en el frontmatter YAML del bloque.
> - El audio se guarda como `dia/audio/YYYY-MM-DD/HH-MM-SS_{autor}.opus`.
> - El JWT de auth lleva `sub: angel|africa` (campo del payload).

---

## `dia_capturar`

Persiste una nota en el archivo del día, clasifica con Haiku y devuelve
el resumen de la operación.

**Signature**:

```python
@mcp.tool()
def dia_capturar(
    texto: str = "",
    audio_b64: str = "",
    ts_iso: str = "",
    etiqueta: str = "auto",
    origen: str = "otro",
    device_label: str = "mcp_directo",
) -> str:
    """
    Captura una nota del día de Angel en el vault.

    Args:
        texto: Texto ya transcrito. Si vacío y audio_b64 viene, se transcribe.
        audio_b64: Audio Opus en base64. Si viene, se transcribe con Whisper.
        ts_iso: Timestamp ISO 8601 del momento de dictado. Vacío = ahora().
        etiqueta: Etiqueta forzada o "auto" (default) → clasifica con Haiku.
        origen: 'voz_movil' | 'voz_linux' | 'texto_directo' | 'otro'.
        device_label: Identificador del dispositivo origen (para trazabilidad).

    Returns:
        JSON string con: {
            "ok": bool,
            "archivo": "knowledge_base/angel/dia/YYYY-MM-DD.md",
            "ts": "ISO",
            "etiqueta_aplicada": "...",
            "confianza": 0.0..1.0,
            "modelo": "...",
            "audio_persistido": "path o null"
        }
    """
```

**Validaciones**:
- `texto` o `audio_b64`: al menos uno debe venir no-vacío. Si no, devuelve
  `{"ok": false, "error": "input_vacio"}`.
- `etiqueta`: debe ser `auto` o una de las 6 válidas, sino fallback `otro`.
- `origen`: si no es uno de los 4 válidos, normaliza a `otro`.
- `ts_iso`: si viene malformado, fallback a `datetime.now(tz=Europe/Paris).isoformat()`.

**Comportamiento**:
1. Si llega `audio_b64`, decodifica y guarda en
   `dia/audio/YYYY-MM-DD/HH-MM-SS.opus`. Transcribe con `faster-whisper`
   modelo `small`. Si el texto resultante está vacío, devuelve error.
2. Llama a Haiku con el prompt de `prompts/clasificar_nota.md` para
   etiquetar (timeout 3s; si excede o falla → etiqueta `otro`,
   confianza `0.0`, modelo `fallback`).
3. Escribe la entrada en `dia/YYYY-MM-DD.md` siguiendo el esquema de
   `data-model.md §1`. Si el archivo no existe, lo crea con cabecera.
4. Si llegan notas con `ts` anteriores a otras ya presentes, reordena
   el archivo por `ts` antes de escribirlo.
5. Devuelve el JSON con los detalles.

**Idempotencia**: Si llega exactamente el mismo `(ts_iso, texto)` ya
presente en el archivo del día, no se duplica y `ok=true` con `nota:
"duplicado_ignorado"`. Esto cubre reintentos de la PWA tras fallo de red.

**Logging**: Cada llamada loguea bajo `/home/nosvers/logs/voz_capturar.log`
con `ts, device_label, origen, etiqueta_aplicada, latencia_ms, ok`. NUNCA
loguea el texto de la nota (privacidad).

---

## `dia_contexto`

Devuelve síntesis sintética del contexto reciente para consumir como
prompt enriquecido.

**Signature**:

```python
@mcp.tool()
def dia_contexto(
    rango_dias: int = 7,
    incluir_calendario: bool = True,
    incluir_estado_agentes: bool = True,
    etiquetas_filtro: str = "",
) -> str:
    """
    Síntesis del contexto reciente de Angel.

    Args:
        rango_dias: 1..30 días hacia atrás. Default 7.
        incluir_calendario: si True, intenta leer eventos próximos.
        incluir_estado_agentes: si True, incluye salida resumida de
            agentes_estado() existente.
        etiquetas_filtro: CSV de etiquetas a incluir (vacío = todas).

    Returns:
        JSON string con: {
            "ok": bool,
            "rango": {"desde": "YYYY-MM-DD", "hasta": "YYYY-MM-DD"},
            "notas_count": int,
            "sintesis": "<texto markdown>",
            "calendario": [...] | "no_disponible",
            "agentes": "..." | null
        }
    """
```

**Comportamiento**:
1. Lee todos los archivos `dia/YYYY-MM-DD.md` del rango.
2. Si `etiquetas_filtro`, parsea las notas y filtra por etiqueta.
3. Si `incluir_calendario`, intenta consultar Google Calendar a través del
   método existente del proyecto (vía MCP o helper). Si falla,
   `calendario: "no_disponible"` y sigue.
4. Si `incluir_estado_agentes`, invoca `agentes_estado()` interno y resume.
5. Pasa todo el material a Claude (Sonnet, balance coste/calidad) con
   prompt de síntesis pidiendo respuesta markdown estructurada de
   máximo 800 palabras.
6. Devuelve el JSON.

**Cache**: Si la misma consulta exacta se repite en < 5 minutos, devuelve
el resultado cacheado (memoria del proceso).

---

## `dia_buscar`

Búsqueda textual en las notas del día con filtro opcional por fechas.

**Signature**:

```python
@mcp.tool()
def dia_buscar(
    query: str,
    desde: str = "",
    hasta: str = "",
    limite: int = 20,
    etiqueta: str = "",
) -> str:
    """
    Búsqueda textual en las notas del diario de Angel.

    Args:
        query: Término o frase a buscar (case-insensitive, sin diacríticos).
        desde: Fecha ISO YYYY-MM-DD inclusive. Vacío = ilimitado pasado.
        hasta: Fecha ISO YYYY-MM-DD inclusive. Vacío = hoy.
        limite: Máximo de coincidencias a devolver. Default 20, max 100.
        etiqueta: Si viene, sólo notas con esa etiqueta.

    Returns:
        JSON string con: {
            "ok": bool,
            "query": "...",
            "rango": {"desde": "...", "hasta": "..."},
            "total": int,
            "resultados": [
                {
                    "fecha": "YYYY-MM-DD",
                    "ts": "ISO",
                    "etiqueta": "...",
                    "fragmento": "...frase con <mark>match</mark>..."
                },
                ...
            ]
        }
    """
```

**Comportamiento (MVP)**:
1. Glob los archivos `dia/*.md` del rango.
2. Para cada archivo, parsea las notas (split por `---`).
3. Para cada nota cuyo texto contenga `query` (normalización: lower +
   `unidecode`), genera un fragmento de ~80 caracteres alrededor de la
   primera coincidencia con `<mark>` envolvente.
4. Si `etiqueta`, filtra por etiqueta de la nota.
5. Ordena resultados por `ts` descendente.
6. Limita por `limite` y devuelve.

**Migración futura a SQLite FTS5**: cuando se supere 1k notas o la
búsqueda lineal exceda 3s, se introduce el cache `dia_search.sqlite` y
esta función pasa a consultarlo (regenerable desde markdown).

---

## Errores comunes (todos los tools)

| Código | Significado | HTTP equivalente |
|---|---|---|
| `input_vacio` | Falta input mínimo (texto o audio). | 400 |
| `parametro_invalido` | Enum o tipo mal pasado. | 400 |
| `vault_locked` | Otro proceso bloquea el archivo, tras 3 reintentos. | 503 |
| `clasificador_timeout` | Haiku > 3s. Se aplica fallback `otro`. | 200 con warning |
| `whisper_error` | Transcripción falló. | 500 |
| `calendario_no_disponible` | Solo info, no es error. | 200 |
| `interno` | Excepción no controlada (loguea trace). | 500 |
