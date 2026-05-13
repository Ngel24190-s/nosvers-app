# NosVers Agent — Roadmap de Auto-Evolución

> Este documento es tu plan de crecimiento. Léelo cada día.
> Implementa el siguiente paso pendiente, testéalo, y avisa a Angel por Telegram.
> Si un paso falla, documenta por qué en la vault y pasa al siguiente.

## Estado: Marca con [x] lo completado

### FASE 2: Migrar agentes como tools internos
- [x] Leer /legacy/agents/agt05_africa.py → extraer lógica → crear tool africa_briefing
- [ ] Leer /legacy/agents/agt_eisenia.py → crear tool eisenia_check
- [ ] Leer /legacy/agents/agt_berger.py → crear tool berger_status
- [ ] Leer /legacy/agents/agt04_seo.py → crear tool seo_generate
- [ ] Leer /legacy/agents/agt02_instagram.py → crear tool instagram_prepare
- [ ] Leer /legacy/agents/agt08_facebook.py → crear tool facebook_prepare
- [ ] Leer /legacy/agents/agt07_youtube.py → crear tool youtube_content
- [ ] Leer /legacy/agents/agt_analyste.py → crear tool weekly_analysis
- [ ] Leer /legacy/agents/agt_directeur.py → crear tool strategic_review
- [ ] Leer /legacy/agents/agt_infra.py → crear tool infra_check
- [ ] Leer /legacy/agents/agt_ingham.py → crear tool ingham_analysis
- [ ] Leer /legacy/agents/agt01_visual.py → crear tool visual_content
- [ ] Leer /legacy/agents/agt06_infoproduct.py → crear tool infoproduct_check
- [ ] Leer /legacy/agents/orchestrator.py → crear scheduler interno (APScheduler)
- [ ] Implementar heartbeat: enviar pulso diario a Angel por Telegram

### FASE 3: Auto-extensión
- [ ] Implementar create_tool: escribir Python, validar, registrar dinámicamente
- [ ] Implementar list_tools: inventario de capacidades disponibles
- [ ] Implementar schedule_task: programar tareas recurrentes
- [ ] Implementar remove_tool: desinstalar tools
- [ ] Implementar self_update: actualizar su propio código, rebuild Docker, reiniciar
- [ ] Persistir custom tools en /app/custom_tools/ (montaje Docker)

### FASE 4: Voz + sensores
- [ ] STT: recibir voice notes Telegram → faster-whisper → texto
- [ ] TTS: generar respuesta hablada → piper-tts → voice note Telegram
- [ ] Auto-detección: si el input fue voz, responder con voz
- [ ] Preparar tools de sensores (temp, riego, cámara) — interfaz lista para hardware

### MEJORAS CONTINUAS
- [ ] Vault search mejorado: búsqueda semántica con embeddings locales
- [ ] Memoria conversacional persistente: guardar historial en vault por usuario
- [ ] Resumen semanal automático: generar informe de actividad para Angel
- [ ] Dashboard web: mini web en nosvers.com/agent/ con estado en tiempo real

## Reglas de evolución
1. UN paso por ciclo. No intentes todo a la vez.
2. Testea ANTES de marcar como completado.
3. Si algo falla, no lo fuerces. Documenta y sigue.
4. Avisa a Angel por Telegram de cada paso completado.
5. Nunca rompas lo que ya funciona.
6. Haz backup antes de cada cambio significativo.

### OPTIMIZACIÓN: Enrutar inferencia por Max subscription
- [ ] Cambiar agent core para usar `claude -p` via subprocess en vez de API directa
- [ ] Patrón: `echo "prompt" | claude -p --output-format json` → parsear respuesta
- [ ] Fallback: si claude -p falla (rate limit, timeout), usar API key como backup
- [ ] Esto elimina el coste de API (~20EUR/mes) — todo cubierto por Max 5x
- [ ] NOTA: solo funciona para uso personal (Angel + África). No escalar a público.
- [ ] Implementar adaptador en core/agent.py: def call_claude() intenta Max primero, API después

### FEATURE HUERTO TRACKING (pendiente — alta prioridad Angel+África)
- [ ] Leer /home/nosvers/public_html/knowledge_base/operaciones/huerto-tracking-blueprint.md
- [ ] Ejecutar Paso 1 del blueprint: migración SQL (huerto_entradas + huerto_precios_ref)
- [ ] Ejecutar Paso 2: patch api.php con 6 nuevos endpoints
- [ ] Ejecutar Paso 3: tests curl de los endpoints
- [ ] Ejecutar Paso 4: patch de la página /granja (HTML+CSS+JS en especialista Potager)
- [ ] Ejecutar Paso 5: test UI en producción (móvil+desktop)
- [ ] Ejecutar Paso 6: tool precios_huerto_scan.py + scheduler lunes 06:00
- [ ] Ejecutar Paso 7: documentación vault/huerto/README.md + notificar a Angel

## 2026-Q2 — Asistente de Voz Personal NosVers (feature 001-voice-assistant)
**Status (2026-05-13):** server-side completo + agente diario + PWA desplegada. Wake word
custom Linux pendiente de entrenamiento Colab (Angel).

**Componentes desplegados:**
- (a) Tools MCP server-side: `dia_capturar`, `dia_contexto`, `dia_buscar` con auth Bearer
  JWT (issue_token.py / revoke_token.py) y REST en `voz/rest.py`.
- (d) Agente `agt07_diario` cron 23:30 (resumen diario Haiku) + 22:00 domingo
  (resumen semanal Opus). Purga audio cron 03:00 (>7d).
- (b) Búsqueda histórica + contexto on-demand (cache TTL 5min).
- (c) PWA `public_html/voz/` con push-to-talk, IndexedDB queue, Background Sync,
  onboarding multi-usuario (Angel/África). URL: https://nosvers-voz.72.61.160.108.nip.io/
- Multi-usuario refactor R1-R9: pool común `dia/`, frontmatter con `autor: angel|africa`,
  audios sufijados `_{autor}.opus`. 65/65 tests passing tras refactor.
- Cliente Linux casa (US3): código completo en `~/nosvers-voz-linux/`. PENDING_T056
  (Angel entrena Claudio wake word en Colab Pro).

**Specs:**
- `specs/voice-assistant-nosvers/specs/001-voice-assistant/{spec,plan,tasks,data-model}.md`
- BRIEF: `specs/voice-assistant-nosvers/BRIEF.md`
- Quickstart: `specs/voice-assistant-nosvers/specs/001-voice-assistant/quickstart.md`

**Próximos pasos:**
- T056: Angel entrena wake word "Claudio" en Colab Pro (~75-90min en T4).
- T031: smoke test PWA en Android Angel.
- voz.nosvers.com: crear DNS A → 72.61.160.108 (opcional, ya hay nip.io HTTPS).
