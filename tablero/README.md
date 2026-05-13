# tablero — Second Brain Dashboard NosVers

Backend FastAPI/Starlette + frontend React+Vite+Tailwind+shadcn que sirve de vista visual
sobre el vault markdown `/home/nosvers/public_html/knowledge_base/`.

## Arquitectura

```
tablero/
├── rest.py             # Routes Starlette montadas en uvicorn de mcp_server.py
├── timeline.py         # Lectura del vault para timeline (Fase A)
├── nota.py             # Lectura individual de una nota (Fase A)
├── log.py              # Logging estructurado + alertas Telegram
├── v2/                 # Fase B+C — escritura + features Notion-clone
│   ├── atomic_write.py    # Escritura atómica tmp+rename (D-013)
│   ├── frontmatter.py     # Parser YAML preservando timestamps
│   ├── slug_resolver.py   # Resolución wiki-link slug (D-002, D-012)
│   ├── concurrency.py     # If-Match → 409 (D-003)
│   ├── wiki_index.py      # Índice in-memory de backlinks (D-004)
│   ├── dia_io.py          # IO a nivel de entrada en archivos-por-día
│   ├── capturar.py        # POST /v2/capturar (US1)
│   ├── editar.py          # PATCH /v2/nota (US2)
│   ├── archivar.py        # POST /v2/nota/archivar y /restaurar (US3)
│   ├── proyectos.py       # GET+PATCH /v2/proyectos (US6 kanban)
│   ├── wiki_endpoint.py   # GET /v2/wiki-index (US7)
│   ├── vault_tree.py      # GET /v2/vault/tree (US8)
│   ├── infra.py           # GET /v2/infra/status (US10)
│   └── agentes.py         # POST /v2/agentes/ejecutar + /catalogo (US11)
├── tests/              # pytest — 131 tests verdes (25 Fase A + 106 nuevos)
└── web/                # Frontend Vite+React+TypeScript
    └── src/
        ├── pages/Dashboard.tsx       # Composición principal
        ├── pages/Login.tsx
        ├── components/               # 25+ componentes de UI
        ├── hooks/                    # useKeyboardShortcut, useVistaPersist, etc.
        └── lib/                      # api, auth, cache, markdown, types
```

## Endpoints

### Fase A (read-only — sin cambios)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tablero/api/health` | Liveness, no auth |
| GET | `/tablero/api/whoami` | Decode JWT |
| GET | `/tablero/api/timeline` | Lista entradas mezcladas Angel + África |
| GET | `/tablero/api/buscar` | Full-text proxy a `voz.buscar` |
| GET | `/tablero/api/nota` | Detalle de una entrada (path + #ts) |

### Fase B+C (`/v2/` namespace, escritura + features)

| Método | Ruta | Descripción | User Story |
|--------|------|-------------|------------|
| POST | `/tablero/api/v2/capturar` | Crear nota nueva (autor del JWT) | US1 |
| PATCH | `/tablero/api/v2/nota` | Editar entrada con If-Match | US2 |
| POST | `/tablero/api/v2/nota/archivar` | Soft delete con razón | US3 |
| POST | `/tablero/api/v2/nota/restaurar` | Restaurar desde papelera | US3 |
| GET | `/tablero/api/v2/proyectos` | Listar tarjetas kanban | US6 |
| PATCH | `/tablero/api/v2/proyectos` | Cambiar estado / campos | US6 |
| GET | `/tablero/api/v2/wiki-index` | Backlinks `[[slug]]` | US7 |
| GET | `/tablero/api/v2/vault/tree` | Árbol del vault lazy | US8 |
| GET | `/tablero/api/v2/infra/status` | 6 badges de salud | US10 |
| GET | `/tablero/api/v2/agentes/catalogo` | Lista agentes whitelist | US11 |
| POST | `/tablero/api/v2/agentes/ejecutar` | Lanzar agente | US11 |

Pendientes para una siguiente sesión (requieren setup OAuth manual):

| Método | Ruta | Estado |
|--------|------|--------|
| GET/POST | `/tablero/api/v2/google/calendar/events` | US13 — contrato OpenAPI listo |
| GET | `/tablero/api/v2/google/gmail/threads` | US14 — contrato OpenAPI listo |
| POST | `/tablero/api/v2/vault/mkdir` | US8 extra — contrato OpenAPI listo |
| POST | `/tablero/api/v2/vault/move` | US8 extra — contrato OpenAPI listo |

## Decisiones técnicas

15 decisiones documentadas en
`specs/second-brain-dashboard/specs/002-fase-bc-notion-clone/decisions.md` (D-001..D-015).

## Tests

```bash
cd /home/nosvers
VOZ_JWT_SECRET=test-secret pytest tablero/tests/ -v   # innecesario con conftest autouse
pytest tablero/tests/                                  # 131 tests verdes
```

## Build frontend

```bash
cd /home/nosvers/tablero/web
npm install         # solo la primera vez
npm run build       # produce dist/, 651 KB total / 203 KB gzip
npm run dev         # vite dev server :5173 con HMR
```

## Deploy dev

```bash
# Tras build:
sudo rsync -av --delete /home/nosvers/tablero/web/dist/ /var/www/tablero/
sudo systemctl restart uvicorn-nosvers
curl -s https://tablero.72.61.160.108.nip.io/tablero/api/health
```

## Constitución

Plan + constitution check en
`specs/second-brain-dashboard/.specify/memory/constitution.md`. Esta Fase B+C
honra todos los 10 principios (Soberanía, MCP-first, Vault SoT, Reuse 001,
No regresión, paridad multi-user, Stack ligero, Observability, Security
baseline).

## Modelo de datos

Decisión arquitectónica importante: **el vault Fase A usa "1 archivo por día"** con
N entradas inline en `dia/<fecha>.md`. Fase B+C respeta este modelo y opera
a nivel de entrada `(fecha, ts)`. El path canónico de una entrada es
`dia/<fecha>.md#<ts>`. Documentado en
`specs/second-brain-dashboard/specs/002-fase-bc-notion-clone/BLOCKER_ARCHITECTURE.md`.

## Concurrencia

Todas las escrituras usan `If-Match` con `concurrency_token` (modified_at si
existe, sino ts inmutable). 409 stale_modified_at incluye `current_modified_at`
en el body para que el cliente proponga "recargar y volver a aplicar".

## Wiki-links

Soporta sintaxis `[[slug]]` y `[[slug|texto-visible]]` estilo Obsidian.
Renderer en `lib/markdown.tsx` los convierte a buttons clickeables.
El backend mantiene `WikiIndex` in-memory reconstruido en startup y
actualizado write-through tras cualquier operación de escritura.
