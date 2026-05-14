# Clarify — Decisiones tomadas en solitario (Fase 2+3)

Angel pidió: "decide solo si crítico". Aquí van las decisiones críticas
con su justificación, para no parar la implementación.

---

## D1. Modelo exacto y endpoint

**Decisión**: `claude-haiku-4-5` vía REST a
`https://api.anthropic.com/v1/messages`, mismo patrón que
`voz/clasificar.py`. NO usar el SDK Python `anthropic` (evita una dep más
y mantiene homogeneidad con el clasificador existente).

**Razón**: el clasificador ya funciona con este modelo, latencia conocida
~600 ms en VPS, prompt corto cabe en context. El SDK añadiría una dep y
duplicaría el patrón.

---

## D2. Formato JSON de salida del modelo

**Decisión**: el modelo devuelve un único JSON con la forma:

```json
{
  "tool": "gasto_anotar",
  "args": {"monto_eur": 45, "concepto": "gasolina", "categoria": "transporte"},
  "confidence": 0.92,
  "razon": "menciona pago y categoría coche"
}
```

- `tool`: nombre exacto del MCP tool (whitelist 22 + `dia_capturar`).
- `args`: objeto con argumentos primitivos. El router **NO** pone `autor`
  aquí — se inyecta server-side desde el JWT (defensa contra inyección).
- `confidence`: 0..1, float.
- `razon`: <= 12 palabras, debug only.

**Razón**: shape minimalista, igual filosofía que `clasificar_nota`.
Inyectar `autor` server-side cierra una vía de spoofing.

---

## D3. Multi-tool en un dictado

**Decisión**: por ahora, **1 tool por dictado**. Si Angel dice "apunta
leche y huevos", el modelo se permite combinar `item="leche, huevos"` y el
tool `lista_compras_añadir` recibe ambos en `item`. Si dice "apunta leche
y recuérdame ir mañana", se elige el más fuerte (probablemente la lista) y
el otro hilo se pierde — Angel puede repetirlo.

**Razón**: planeación multi-tool añade complejidad significativa
(ordering, parcial failure). Lo dejamos para Fase 4.

---

## D4. Idempotencia

**Decisión**: cache in-process LRU de 64 entradas, TTL 5 s. Key:
`(sha256(transcript)[:16], autor)`. La segunda llamada devuelve
**exactamente** el mismo dict que la primera (incluyendo `tool_result`).

**Razón**: simple, sin Redis. Si el servidor se reinicia el cache se pierde
— es aceptable porque el TTL es 5 s.

---

## D5. Schema WS para canales nuevos

**Decisión**: cada canal publica un dict snapshot completo. No envíos
diff. Coherente con los workers existentes (`health`, `revenue`).

Payload por canal:

| canal | payload |
|---|---|
| recordatorios | `{items: [{slug, texto, fecha, autor, prioridad, hecho}], total_hoy: n, total_semana: n}` |
| gastos | `{mes: "YYYY-MM", total_mes_eur: f, por_categoria: {cat: eur}, delta_vs_anterior_eur: f, n_apuntes: n}` |
| compras | `{items: [{texto, autor, fecha, urgente}], total: n}` |
| medicacion | `{proxima: {quien, medicamento, hora, minutos_hasta}, hoy: [...]}` |
| coche | `{matricula, modelo, km, itv_proxima, itv_dias_falta, ultimo_mantenimiento}` |
| menu_dia | `{dia, comida, cena, ingredientes_destacados: [...]}` |
| bris | `{proxima_vacuna, ultimo_paseo, peso_kg, animo}` |

Si vault vacío: `{"empty": true}` (FR-W-4).

---

## D6. Layout default

**Decisión**: respetar layouts existentes guardados en localStorage. El
merge actual en `useCockpitLayout.ts` (líneas 58-61) ya añade widgets que
falten — basta extender `DEFAULT_LAYOUT` y los usuarios verán los nuevos
en su próxima sesión sin perder posicionamiento.

Posición default propuesta (extendiendo el grid 12 cols):
- y=17: recordatorios(6×4) | compras(3×4) | menu_dia(3×4)
- y=21: gastos(6×4) | coche(3×4) | medicacion(3×4)
- y=25: bris(3×4) — fila propia

**Razón**: no tocar nada por encima de y=17 garantiza que el layout actual
de Angel persiste.

---

## D7. Interacciones optimistas (marcar recordatorio / item)

**Decisión**: en esta fase los widgets son **read-only**. El usuario marca
desde Telegram o desde el bot. Si el budget de tiempo lo permite tras el
core, se añade `POST /tablero/api/v2/action` con shape
`{tool, args}` que delega al tool MCP. Si no, queda como TODO documentado
en INTENT_ROUTER.md.

**Razón**: el "wow" del ciclo lo da la voz → tool → vault → widget, no la
edición desde la UI. Una iteración después se añade.

---

## D8. Persistencia del cache idempotente

**Decisión**: in-memory, módulo-level `dict`. Se pierde al reiniciar.

**Razón**: la idempotencia protege contra doble-tap del usuario, no contra
algo más sofisticado. 5 s en RAM bastan.

---

## D9. Prompt en vault editable

**Decisión**: el prompt del router vive en
`public_html/knowledge_base/prompts/intent_router.md` con frontmatter:
```yaml
---
nombre: intent_router
modelo: claude-haiku-4-5
version: 1
threshold: 0.6
---
```

El router lo carga al import. Si el archivo no existe, usa un prompt
fallback hardcoded en `intent_router.py` (degraded mode).

**Razón**: poder iterar el prompt sin redeployar.

---

## D10. Bug telegram_enviar

**Decisión**: NO usar `telegram_enviar` ni intermedio ni al final. Angel
ya tiene la regla en memoria. Si alguna verificación final lo necesita,
abortar tras 30 s y marcar como `MCP_STALL_RESOLVED_BY_OPUS_MOBILE` en
tasks.md.

---

## D11. Test mock estrategy

**Decisión**: tests del router monkeypatchean `requests.post` para
devolver respuestas Anthropic-shape sintéticas. Cero llamadas reales a la
API. Coverage: 20+ casos.

---

## D12. dia_capturar como fallback

**Decisión**: cuando confidence < 0.6 o tool fuera de whitelist, el
endpoint llama a `voz.capturar.dia_capturar_impl(...)` con el transcript.
El TTS responde "Apuntado en notas."

**Razón**: ya existe, ya funciona, ya tiene CORS y autor desde JWT. No
duplicar lógica.
