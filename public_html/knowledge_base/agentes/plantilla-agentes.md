# Plantilla de Agentes NosVers

> Base de conocimiento NosVers · Gestion operativa
> Responsable: Director Ejecutivo (Claude Code)

---

## Arquitectura

```
Claude Code (Director Ejecutivo)
    |
    ├── ORCHESTRATOR ─── Coordinador central, cada hora
    |
    ├── AGT-01 ───────── Visuels Instagram
    ├── AGT-02 ───────── Copy Instagram
    ├── AGT-03 ───────── YouTube (FASE 2 - inactivo)
    ├── AGT-04 ───────── SEO Blog WordPress
    ├── AGT-05 ───────── Procesamiento conocimiento Africa
    └── AGT-06 ───────── Infoproductos PDF + entrega
```

Todos los agentes residen en `/home/nosvers/agents/` en el VPS Hostinger.
Configuracion compartida via `.env` en el mismo directorio.

---

## ORCHESTRATOR

| Campo | Valor |
|---|---|
| **Archivo** | `agents/orchestrator.py` |
| **Mision** | Coordinador central. Verifica estado de todos los agentes cada hora. |
| **Lee** | `operaciones/semana-actual.md` + logs de cada agente |
| **Escribe** | `operaciones/log-orquestador.md` |
| **Acciones** | Lanza agentes segun prioridad. Notifica Angel via Telegram si hay errores o logros. |
| **Cron** | `0 * * * *` (cada hora en punto) |
| **Estado** | PENDIENTE — esperando despliegue VPS |

---

## AGT-01 — Visuels Instagram

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt01_visual.py` |
| **Mision** | Procesar fotos brutas de Africa en visuels listos para Instagram. |
| **Input** | Fotos en `/home/nosvers/uploads/` o recibidas por email de Africa |
| **Output** | JPEGs procesados en `/home/nosvers/visuels/semana-X/` |
| **Identidad visual** | Paleta #FEFAF4 + #5A7A2E. Tipografia Playfair Display + DM Sans. |
| **Cron** | Activacion manual o por trigger del Orchestrator |
| **Estado** | ACTIVO — esperando fotos de Africa |
| **Dependencia** | Africa envia fotos originales de la ferme |

---

## AGT-02 — Copy Instagram

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt02_instagram.py` |
| **Mision** | Generar 5 posts/semana con copy completo, hashtags y CTA. |
| **Lee** | `contexto/nosvers-identidad.md` + `contexto/angel-filosofia.md` + `operaciones/semana-actual.md` |
| **Escribe** | `agentes/agt02-posts-pendientes.md` |
| **Flujo** | Genera posts → envia a Angel via Telegram para aprobacion → publica |
| **Tono** | Directo, sin positivismo vacio, desde la experiencia real |
| **Cron** | `0 10 * * 0` (domingos 10:00h) |
| **Estado** | ACTIVO — 5 posts S1 generados, pendientes de publicacion |

---

## AGT-03 — YouTube

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt03_youtube.py` |
| **Mision** | Produccion de contenido video para canal YouTube NosVers. |
| **Estado** | FASE 2 — NO activar hasta M3 |
| **Notas** | Requiere que Angel grabe contenido. Planificacion pendiente. |

---

## AGT-04 — SEO Blog WordPress

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt04_seo.py` |
| **Mision** | Articulo de blog semanal optimizado SEO + analisis de keywords. |
| **Lee** | Vault completa para contexto + tendencias de busqueda |
| **Escribe** | Post WordPress en modo draft + `agentes/agt04-seo.md` (keywords, metricas) |
| **API** | WordPress REST API → `POST /wp-json/wp/v2/posts` |
| **Cron** | `0 7 * * 1` (lunes 7:00h) |
| **Estado** | PENDIENTE — esperando credenciales WordPress operativas |

---

## AGT-05 — Conocimiento Africa

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt05_africa.py` |
| **Mision** | Procesar comunicaciones de Africa → estructurar conocimiento → generar contenido para Club. |
| **Input** | Email de africa.sanchez.gomez@gmail.com |
| **Escribe** | `contexto/africa-conocimiento.md` + material base para PDFs del Club |
| **Flujo** | Lee emails → extrae conocimiento → estructura en vault → cuando hay suficiente, trigger a AGT-06 |
| **Cron** | `0 */6 * * *` (cada 6 horas) |
| **Estado** | ACTIVO — email con 5 preguntas enviado a Africa, esperando respuesta |

---

## AGT-06 — Infoproductos PDF

| Campo | Valor |
|---|---|
| **Archivo** | `agents/agt06_infoproduct.py` |
| **Mision** | Generar PDFs maquetados para Club Sol Vivant + configurar venta en Lemon Squeezy + entrega automatica. |
| **Input** | Contenido estructurado de AGT-05 + conocimiento de la vault |
| **Output** | PDF formateado con identidad NosVers → subido a Lemon Squeezy → entrega por email |
| **Identidad** | Paleta NosVers, tipografia Playfair + DM Sans, logo |
| **Estado** | FASE 1 — activar en M1 cuando haya contenido suficiente |

---

## Tabla resumen

| Agente | Cron | Estado | Prioridad |
|---|---|---|---|
| Orchestrator | `0 * * * *` | Pendiente | CRITICA |
| AGT-01 Visual | Manual/trigger | Esperando fotos | Alta |
| AGT-02 Instagram | Dom 10h | Posts S1 listos | Alta |
| AGT-03 YouTube | -- | FASE 2 (M3) | Baja |
| AGT-04 SEO | Lun 7h | Pendiente creds | Media |
| AGT-05 Africa | Cada 6h | Esperando respuesta | Alta |
| AGT-06 PDF | Manual/trigger | FASE 1 | Media |

---

## Protocolo de fallos

1. **Agente no ejecuta:** Orchestrator detecta → log + alerta Telegram a Angel
2. **Error de API:** Reintentar 3 veces con backoff → si persiste, alerta
3. **Agente produce basura:** Orchestrator revisa calidad minima → descarta + alerta
4. **Falta de input:** Marcar en log, no fabricar contenido falso

**Regla:** Nunca publicar contenido sin aprobacion de Angel (excepto logs internos).

---

## Despliegue

```bash
# Estructura en VPS
/home/nosvers/agents/
    ├── .env                    # Credenciales (no en GitHub)
    ├── orchestrator.py
    ├── agt01_visual.py
    ├── agt02_instagram.py
    ├── agt03_youtube.py        # Placeholder
    ├── agt04_seo.py
    ├── agt05_africa.py
    ├── agt06_infoproduct.py
    └── logs/
        └── [agente]-[fecha].log
```

Crontabs gestionados via `crontab -e` del usuario `nosvers` en el VPS.

---

*NosVers · Plantilla de Agentes · Mars 2026*
