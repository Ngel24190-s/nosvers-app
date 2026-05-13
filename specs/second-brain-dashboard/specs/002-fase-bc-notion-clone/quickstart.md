# Quickstart — Fase B+C (Notion-clone real)

Guía mínima: del checkout al smoke test productivo. Si fallas en algún paso, revisa `decisions.md` y `research.md` antes de improvisar.

## 0. Prerrequisitos verificados

```bash
# Backend
python3 --version            # ≥ 3.11
ls /home/nosvers/voz/        # debe existir (proyecto 001)
ls /home/nosvers/tablero/    # debe existir (Fase A)
cat /home/nosvers/voz/auth.py | head -20  # JWT helpers presentes

# Frontend
cd /home/nosvers/tablero/web
cat package.json | grep '"react"'
node --version               # ≥ 20

# Vault
ls /home/nosvers/public_html/knowledge_base/dia/ | head
```

## 1. Instalar nuevas dependencias

### Backend

```bash
cd /home/nosvers
pip install httpx google-auth pyyaml  # pyyaml ya está; httpx y google-auth nuevos
# Si pyproject.toml está pinado:
pip install -e .[v2]
```

### Frontend

```bash
cd /home/nosvers/tablero/web
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities d3-force d3-selection d3-zoom cmdk dompurify
npm install -D @types/d3-force @types/dompurify playwright
npm run build         # debe pasar sin warnings nuevos
```

## 2. Configurar OAuth Google (una vez)

Angel ejecuta una sola vez:

```bash
# Crea credenciales OAuth Web App en console.cloud.google.com (Calendar API + Gmail API)
# Descarga el client_secret.json a /tmp/google_client_secret.json

python3 /home/nosvers/tablero/v2/scripts/google_oauth_setup.py \
  --client-secret /tmp/google_client_secret.json \
  --scopes calendar.events gmail.readonly gmail.send \
  --out /etc/nosvers/secrets/google.json

sudo chmod 0600 /etc/nosvers/secrets/google.json
sudo chown root:root /etc/nosvers/secrets/google.json
```

El script abre el navegador local, pide consent, captura el refresh token y lo guarda en el path final con perms correctos.

## 3. Reconstruir índices y arrancar dev

```bash
# Backend dev
cd /home/nosvers
TABLERO_DEV=1 python3 -m tablero.scripts.dev_server
# → uvicorn levanta en :8000 con /tablero/api/* (Fase A) y /tablero/api/v2/* (Fase B+C)
# → Reconstruye el wiki-index en startup (ver log "wiki_index: built N entries in M.M ms")

# Frontend dev en otra terminal
cd /home/nosvers/tablero/web
npm run dev
# → Vite levanta en :5173 con HMR
```

Abrir `http://localhost:5173`. Autenticarse con JWT angel o africa (mismo flujo Fase A).

## 4. Smoke test mínimo (manual)

Hacer cada uno y marcar OK / FAIL:

| Paso | Esperado | Status |
|---|---|---|
| `Ctrl+N` abre modal captura | Modal centrado, input focused | [ ] |
| Capturar nota "smoke test 1" + etiqueta `idea` | Aparece arriba del timeline en ≤ 1 s | [ ] |
| Verificar `knowledge_base/dia/<hoy>-smoke-test-1.md` existe | `cat` muestra frontmatter `autor: angel` (o africa) | [ ] |
| Clic en la nota → "Editar" → cambiar palabra → guardar | Cambio refleja en el timeline | [ ] |
| `Ctrl+K` abre command palette | Paleta centrada con secciones Notas/Proyectos/Acciones | [ ] |
| Teclear "smoke" en palette → Enter | Navega a la nota detalle | [ ] |
| Cambiar vista a Tabla/Kanban/Calendario/Galería | Cada una renderiza ≤ 200 ms | [ ] |
| Archivar la nota smoke → confirmar | Desaparece del timeline | [ ] |
| Abrir Papelera del sidebar | Nota aparece archivada | [ ] |
| Restaurar | Reaparece en timeline con contenido intacto | [ ] |
| Abrir Sidebar tree → ver `dia/`, `proyectos/`, `contexto/` | Estructura coincide con `ls knowledge_base/` | [ ] |
| Abrir vista Proyectos → ver kanban (si no existe carpeta, debe crearla con bienvenida.md) | 4 columnas + 1 tarjeta inicial | [ ] |
| Crear `proyectos/test.md` manualmente con `estado: todo`, recargar | Tarjeta aparece en `todo` | [ ] |
| Drag tarjeta a `doing` | Frontmatter se actualiza; `cat proyectos/test.md \| grep estado` muestra `doing` | [ ] |
| Editar otra nota teclear `[[smoke-test-1]]` y guardar | El enlace aparece clicable | [ ] |
| Abrir `smoke-test-1` → ver sección "Referenciada desde" | Aparece la nota que la referencia | [ ] |
| Abrir vista Grafo (necesita ≥ 5 wiki-links para verse interesante) | Render < 2 s, nodos visibles | [ ] |
| Abrir Sidebar Infra | 6 badges aparecen | [ ] |
| Pulsar botón "ejecutar agt07_diario" | Spinner → output del agente en panel | [ ] |
| Abrir Sidebar Calendar (con OAuth configurado) | Próximos 7 días con eventos | [ ] |
| Abrir Sidebar Gmail | Hilos prioritarios con snippet | [ ] |
| Stats widget | Conteo notas por autor de la semana | [ ] |

Si todos OK → Fase B+C smoke pasa.

## 5. Verificar no-regresión Fase A

```bash
cd /home/nosvers
pytest tablero/tests/test_auth_gate.py tablero/tests/test_timeline.py \
       tablero/tests/test_buscar_proxy.py tablero/tests/test_nota_path_safety.py -v
# Esperado: 78 passed (sin cambios desde Fase A)
```

Si algún test Fase A falla, **REVERT y diagnosticar**. La Constitución V exige zero regresión.

## 6. Verificar nuevos tests Fase B+C

```bash
pytest tablero/tests/test_v2_* -v --cov=tablero/v2 --cov-report=term
# Esperado: 100% pass, coverage ≥ 80%
```

## 7. Lighthouse smoke (perf budget)

```bash
cd /home/nosvers/tablero/web
npx lighthouse http://localhost:5173 \
  --preset=mobile --throttling.cpuSlowdownMultiplier=4 \
  --only-categories=performance \
  --output=json --output-path=./lighthouse.json
jq '.audits["interactive"].numericValue' lighthouse.json
# Esperado: < 2000 ms (2 s). SC-008.
```

## 8. Deploy a dev (`tablero.72.61.160.108.nip.io`)

```bash
# 1. Build frontend
cd /home/nosvers/tablero/web
npm run build
# → produce tablero/web/dist/

# 2. Copiar a nginx doc-root
sudo rsync -av --delete /home/nosvers/tablero/web/dist/ /var/www/tablero/

# 3. Reiniciar uvicorn para cargar rutas v2
sudo systemctl restart uvicorn-nosvers

# 4. Verificar health
curl -s https://tablero.72.61.160.108.nip.io/tablero/api/health
# → {"ok": true, "service": "tablero", "version": "0.2.0"}

# 5. Smoke remoto (con JWT real)
TOKEN="<JWT angel>"
curl -s -H "Authorization: Bearer $TOKEN" \
  https://tablero.72.61.160.108.nip.io/tablero/api/v2/wiki-index | jq '.generated_at'
```

## 9. Rollback (si algo va mal)

```bash
# Backend: revertir el commit que añadió tablero/v2/* y rest.py
cd /home/nosvers
git log --oneline | head -20
git revert <commit_hash>
sudo systemctl restart uvicorn-nosvers

# Frontend: revertir el bundle al estado Fase A
sudo rsync -av --delete /home/nosvers/tablero/web/dist-fase-a-backup/ /var/www/tablero/
# (Antes del deploy haz una copia: sudo cp -a /var/www/tablero /var/www/tablero-fase-a-backup)
```

Los archivos en `knowledge_base/` NO se revierten — son source of truth y cualquier nota capturada queda guardada. Eso es deseado.

## 10. Notificar a Angel

Al cerrar Fase B+C:

```bash
# Usar el MCP nosvers o el bot directamente
python3 -c "
import os, requests, json
token = os.environ['TELEGRAM_TOKEN']
chat = '5752097691'
msg = '''🌿 Fase B+C cerrada — Notion-clone real desplegado.

✅ 14/14 sub-componentes implementados
✅ 78 tests Fase A + N nuevos pasando
✅ Lighthouse < 2s sobre 4G
✅ Deploy dev: https://tablero.72.61.160.108.nip.io

Cambios manuales pendientes (si los hay):
- ...

Push manual cuando quieras revisar: \`git log --oneline\` → push a main.'''
requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
              json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
"
```

Si la tool MCP `telegram_enviar` se cuelga > 30 s (bug conocido), abortar y reintentar una sola vez; si persiste, dejar en logs `MCP_STALL_FASE_BC` y enviar Angel manualmente.

---

*Quickstart Fase B+C · 2026-05-13*
