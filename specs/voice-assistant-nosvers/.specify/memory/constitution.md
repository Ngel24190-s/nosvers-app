<!--
SYNC IMPACT REPORT
==================
Version change: (template) → 1.0.0
Bump rationale: Initial ratification of the project constitution from the
populated template. No prior versioned constitution existed, so this is the
baseline (MAJOR.MINOR.PATCH = 1.0.0).

Principles defined (all new):
  I.   Soberanía Tecnológica
  II.  MCP-First
  III. El Vault es la Verdad
  IV.  No Regresión sobre Infraestructura Existente
  V.   Privacidad por Defecto

Added sections:
  - Restricciones Operativas
  - Flujo de Desarrollo y Calidad
  - Governance

Removed sections: none (template had no prior concrete content).

Templates and docs reviewed:
  - .specify/templates/plan-template.md ✅ compatible (generic Constitution
    Check gate — no rename required; principles will be evaluated at gate
    time by /speckit-plan)
  - .specify/templates/spec-template.md ✅ compatible (no constitution-tied
    sections need rename)
  - .specify/templates/tasks-template.md ✅ compatible (task categorization
    flexible enough to absorb principle-driven tasks like MCP-tool, vault
    schema, observability/log rotation, privacy purge cron)
  - .specify/templates/checklist-template.md ✅ compatible (no changes)
  - BRIEF.md ✅ aligned (constitution principles derived directly from it)
  - CLAUDE.md (project-local at specs/voice-assistant-nosvers/) ✅ compatible
  - CLAUDE.md (parent /home/nosvers/) ✅ compatible — no governance conflict

Deferred TODOs: none.
-->

# Asistente de Voz Personal NosVers — Constitution

## Core Principles

### I. Soberanía Tecnológica

Todo componente nuevo MUST preferir software open-source y procesamiento local
cuando exista alternativa viable. STT (speech-to-text), TTS (text-to-speech) y
detección de wake word DEBEN ejecutarse on-device u on-VPS por defecto
(Whisper.cpp, Kokoro / F5-TTS, openWakeWord o equivalente). La API de Anthropic
es la única dependencia cloud aceptada por defecto (es el cerebro del sistema);
cualquier otra dependencia cloud propietaria (ElevenLabs, transcripciones SaaS,
etc.) SOLO se introduce si una alternativa local ha sido evaluada y descartada
con justificación explícita registrada en el plan de la feature.

**Rationale**: NosVers se construye como infraestructura propia precisamente
porque vendor lock-in y dependencias opacas contradicen el destino del
proyecto (soberanía real). Cada nodo externo no auditado es una grieta en
esa soberanía.

### II. MCP-First

Toda funcionalidad nueva accesible a Angel desde voz, móvil o cliente local
MUST exponerse como herramienta del servidor MCP `nosvers-mcp-2026`. Endpoints
REST aislados, scripts ad-hoc no expuestos por MCP o duplicados de tools ya
existentes están PROHIBIDOS. Los 12 tools actuales del MCP (`sistema_estado`,
`ejecutar_comando`, `git_pull_vps`, `deploy_vps`, `agente_ejecutar`,
`agente_logs`, `agentes_estado`, `telegram_enviar`, `vault_leer`,
`vault_escribir`, `vault_listar`, `wp_crear_post`) son la línea de base — las
extensiones (`dia_capturar`, `dia_contexto`, `dia_buscar` y cualquier otra que
surja) DEBEN ampliar ese mismo servidor.

**Rationale**: Una única superficie MCP da un punto de auditoría, un punto de
versionado y un único contrato consumible por todos los clientes (Claude Code,
PWA, Claude app móvil). Múltiples APIs paralelas dispersan ese contrato y
multiplican la superficie de fallo.

### III. El Vault es la Verdad

`/home/nosvers/public_html/knowledge_base/` MUST ser la única fuente de verdad
para estado persistente legible por humanos: notas dictadas, resúmenes,
prompts, contexto. Está PROHIBIDO crear bases de datos paralelas o silos de
estado fuera del vault para datos que un humano podría querer leer/editar.
SQLite y similares SE PERMITEN únicamente para índices/caches derivables y
reconstruibles desde el vault (búsqueda full-text, embeddings) y MUST poder
regenerarse desde cero ejecutando un único script idempotente.

**Rationale**: El vault es markdown puro, versionable en git, sincronizable a
Obsidian, editable a mano por Angel desde el móvil. Cualquier dato encerrado
en un binario propietario o tabla SQL deja de ser propiedad real del usuario.

### IV. No Regresión sobre Infraestructura Existente

El unified-agent, los agentes cron (`agt01_visual`, `agt02_instagram`,
`agt04_seo`, `agt05_africa`, `agt_directeur`, `agt_eisenia`, `agt_infra`,
etc.), el bot Telegram, WordPress + WooCommerce y el sitio `nosvers.com` NO
SE TOCAN salvo para añadir tools nuevos al MCP server. Cualquier cambio en
estos sistemas existentes MUST ser estrictamente aditivo (nuevo endpoint,
nuevo tool, nuevo agente bajo `/home/nosvers/agents/agt07_diario/` etc.) y
reversible con un único git revert + reinicio de servicio. Modificaciones
que alteren el comportamiento observable de un componente existente DEBEN
declararse como violación en el bloque "Complexity Tracking" del plan con
mitigación documentada.

**Rationale**: Hay ingresos en marcha (Stripe live, Club Sol Vivant, ventas
WooCommerce) y agentes corriendo en cron. Una regresión silenciosa en el
unified-agent o en WordPress es pérdida directa de dinero o de confianza.

### V. Privacidad por Defecto

Audio capturado desde dictado MUST tener TTL máximo de 7 días — un cron
nightly lo borra automáticamente. El transcript queda como verdad
permanente. Cualquier dato que salga del VPS hacia una API externa
(Anthropic incluida) MUST limitarse al texto estrictamente necesario para la
tarea; está PROHIBIDO enviar audio crudo, vault completo, listas de
contactos o credenciales a servicios externos. La PWA y el cliente Linux
MUST autenticarse con tokens revocables almacenados localmente, no con
credenciales reutilizables. Logs del sistema bajo `/home/nosvers/logs/` MUST
rotar y MUST redactar tokens y secretos antes de persistirse.

**Rationale**: Angel dicta pensamientos personales, contexto familiar,
movidas mentales. Esa información solo tiene sentido si se mantiene bajo su
control. Las fugas son irreversibles; los TTLs y la minimización son la
única defensa real.

## Restricciones Operativas

- **Sandboxing**: Todo servicio nuevo MUST correr dentro del Dockerfile del
  unified-agent o como contenedor propio. Procesos sueltos en el host
  PROHIBIDOS (excepción tasada: cron jobs del sistema que ya siguen el
  patrón establecido en `/home/nosvers/agents/`).
- **Logs**: Toda pieza nueva MUST escribir bajo `/home/nosvers/logs/` con
  rotación configurada (logrotate o equivalente) y nivel de detalle
  ajustable por variable de entorno.
- **Idempotencia**: Scripts de deploy, instalación, migración y borrado MUST
  ser idempotentes — ejecutarlos dos veces seguidas no rompe nada.
- **Reproducibilidad**: Dependencias congeladas (uv lock, requirements
  pinneados, imágenes Docker tagged por SHA, no `latest`).
- **Stack base**: Python 3.12+ con `uv` para gestión de dependencias.
  TypeScript permitido únicamente para componentes cliente (PWA) donde
  Python no es opción.
- **Idioma del producto**: Castellano por defecto para la interacción con
  Angel. Francés disponible cuando se trabaja contenido público NosVers. El
  código y los comentarios técnicos MAY estar en inglés; los mensajes de
  voz, prompts del usuario y documentación de usuario final MUST estar en
  español castellano.

## Flujo de Desarrollo y Calidad

- **Spec Kit obligatorio**: Toda feature MUST atravesar el flujo
  `/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. Saltarse fases
  REQUIERE justificación explícita registrada en `spec.md`.
- **Constitution Check**: El gate "Constitution Check" del plan template MUST
  validar explícitamente los 5 principios antes de permitir Phase 0 y de
  nuevo tras Phase 1. Violaciones MUST aparecer en "Complexity Tracking"
  con la razón y la alternativa más simple rechazada.
- **Revisión de seguridad antes de cliente**: Cuando se complete la
  implementación server-side (MCP tools nuevos + agente `agt07_diario`) y
  ANTES de comenzar trabajo en clientes (PWA Android, cliente Linux voz),
  el sistema MUST notificar a Angel vía Telegram para que Claude Opus
  ejecute una revisión de seguridad sobre la infraestructura existente.
- **Despliegue**: Cambios server-side se despliegan vía `git_pull_vps` o
  `deploy_vps` del MCP existente. No se introduce nueva tooling de deploy.
- **Testing**: Cada tool MCP nuevo MUST tener al menos una prueba de
  contrato (entrada → salida esperada) y una prueba de integración contra
  el vault real bajo `knowledge_base/`. Cobertura adicional al gusto del
  implementador.
- **Observabilidad**: Cada agente y servicio nuevo MUST exponer su estado
  vía `agentes_estado` o `sistema_estado` del MCP. Estado opaco está
  PROHIBIDO.

## Governance

Esta constitution prevalece sobre cualquier práctica, convención o atajo
adoptado durante la implementación. Conflictos entre esta constitution y
otros documentos (CLAUDE.md, BRIEF.md, README) se resuelven a favor de la
constitution; el documento conflictivo MUST actualizarse en el mismo PR.

**Procedimiento de enmienda**:
1. Propuesta escrita en el PR o comentario que la introduce, con
   justificación.
2. Bump de versión según semver:
   - MAJOR: eliminación o redefinición incompatible de un principio.
   - MINOR: añadido de principio o sección, expansión material de guía.
   - PATCH: clarificaciones, redacción, correcciones no semánticas.
3. Aprobación explícita de Angel (CEO) registrada en el PR.
4. Sync Impact Report en el HTML comment inicial del archivo, listando
   plantillas/documentos afectados.

**Cumplimiento**:
- Todo PR y toda generación de plan MUST verificar conformidad con los 5
  principios. La verificación es responsabilidad del agente que ejecute
  `/speckit-plan` y del code-reviewer humano (Angel) o asistido (Claude
  Opus revisión).
- Complejidad añadida MUST justificarse en "Complexity Tracking".
- Guidance de runtime para agentes y operadores: ver
  `/home/nosvers/CLAUDE.md` (general NosVers) y
  `/home/nosvers/specs/voice-assistant-nosvers/CLAUDE.md` (proyecto).

**Version**: 1.0.0 | **Ratified**: 2026-05-12 | **Last Amended**: 2026-05-12
