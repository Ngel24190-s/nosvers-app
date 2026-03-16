# estrategia-marketing-agentes
*2026-03-14 11:09*

# NosVers · Estrategia Marketing & Plantilla de Agentes v2
*Revisión completa — 2026-03-14*

## DIAGNÓSTICO ACTUAL

Lo que tenemos funciona como producción de contenido aislada.
Lo que nos falta es un sistema de inteligencia + distribución multicanal coordinada.

La diferencia: pasar de "publicar contenido" a "dominar la conversación sobre suelo vivo en Francia".

---

## ARQUITECTURA DE MARKETING COMPLETA

### El modelo: HUB & SPOKE

```
AGT-00 Intelligence (NUEVO)
        ↓ ideas, tendencias, competitors
AGT-Content Director (NUEVO) ← cerebro estratégico
        ↓ briefings por canal
AGT-02 Instagram  AGT-07 YouTube  AGT-08 Facebook  AGT-04 SEO/Blog
        ↓              ↓               ↓                ↓
     @nosvers      YouTube NosVers   FB NosVers     nosvers.com
        └──────────────────────────────────────────────┘
                    AGT-01 Visual (sirve a todos)
                    AGT-03 Drive (fotos a todos)
```

---

## AGENTES NUEVOS A CREAR

### AGT-00 · Intelligence Collector
**Misión:** Monitorizar la web y alimentar de ideas a todos los agentes de contenido.

**Lo que hace cada día:**
- Scraping de 10-15 blogs franceses de jardinage/permaculture (URLs configurables)
- Monitoriza Google Trends: "lombricompost", "sol vivant", "jardinage biologique france"
- Lee RSS de revistas especializadas: Rustica, La Maison Écologique, etc.
- Monitoriza competidores (sin nombrarlos, solo detectar gaps)
- Extrae artículos de Reddit r/jardinagebiologique, Facebook groups jardinage France
- Detecta preguntas frecuentes en foros → oportunidades de contenido

**Output:**
- `intelligence/ideas-semaine.md` — 10 ideas accionables esta semana
- `intelligence/tendances.md` — tendencias detectadas
- `intelligence/gaps.md` — temas que nadie está cubriendo bien
- Alimenta directamente al AGT-Content Director

**Cron:** `0 6 * * *` (cada mañana 6h)

**Stack:** Python + BeautifulSoup + feedparser + pytrends

---

### AGT-09 · Content Director
**Misión:** El cerebro estratégico. Lee intelligence, define qué publicar en cada canal esta semana, mantiene coherencia de mensaje.

**Lo que hace:**
- Lee `intelligence/ideas-semaine.md` cada domingo
- Lee métricas de cada canal (qué funcionó la semana pasada)
- Genera el "Content Brief Semanal" para todos los agentes
- Asegura que el mismo tema se adapta bien a cada plataforma (no copiar/pegar)
- Mantiene el calendario editorial a 4 semanas vista
- Detecta oportunidades estacionales (época de siembra, etc.)

**Output:**
- `operaciones/brief-semanal.md` → todos los agentes lo leen antes de generar
- `operaciones/calendario-editorial.md` → visión 4 semanas

**Cron:** `0 9 * * 0` (domingos 9h, antes del AGT-02)

**Regla de oro:** Un tema, tres formatos.
```
"La importancia del olor del suelo" (idea de Africa)
    → Instagram: foto manos + tierra + caption corto
    → YouTube: vídeo África oliendo tierra, explicando (60s)
    → Blog: artículo 1200 palabras con science Ingham
    → Facebook: post educativo con infografía simple
```

---

### AGT-02 Instagram v2 · (mejorar el existente)
**Cambios respecto a v1:**

**Antes:** Genera 5 posts genéricos cada semana
**Ahora:** Lee el brief del Content Director + métricas de la semana anterior + tendencias de Intelligence

**Nuevas funcionalidades:**
- Análisis de qué posts funcionaron mejor (engagement rate)
- Genera variaciones de contenido exitoso
- Gestiona las Stories además del feed
- Programa colaboraciones con cuentas jardinage France
- Detecta el mejor momento para publicar según audiencia

**Tipos de contenido ampliados:**
- Feed posts (ya los tiene)
- Stories interactivas (preguntas, encuestas)
- Carruseles educativos (nuevo — alto engagement)
- Reels 15-30s (ya los tiene)
- Collabs con @jardiniers + @permaculteurs Francia

---

### AGT-07 · YouTube Manager
**Misión:** Canal YouTube NosVers — educación profunda sobre suelo vivo.

**Formatos sin voz (África no necesita hablar):**
- Timelapse del lombricompost (24h en 60s)
- Manos de África trabajando + texto superposado
- "Un día en la ferme" — vídeo ambiental con música y textos
- Proceso completo LombriThé (visuales + explicación texto)
- Antes/después de bancales

**Formatos con voz (cuando África quiera):**
- "Pregunta a África" — responde preguntas del Club
- Tutoriales paso a paso
- Visitas a la ferme

**Lo que hace el agente:**
- Genera el guión completo + descripción SEO + tags
- Sugiere la estructura de edición para el vídeo
- Gestiona las descripciones optimizadas para YouTube Search
- Programa publicación (martes 18h — mejor horario jardinage France)
- Responde comentarios simples automáticamente

**Cron:** `0 10 * * 2` (martes 10h — genera briefing semanal)

---

### AGT-08 · Facebook Manager
**Misión:** Facebook es donde está la audiencia de NosVers — jardineros 35-60 años France.

**Por qué Facebook es clave para NosVers:**
Instagram = 25-35 años. Facebook = 40-65 años. La audiencia que tiene huerto y poder adquisitivo está en Facebook.

**Lo que hace:**
- Publica adaptaciones del contenido Instagram (no copias — adaptaciones)
- Gestiona la página NosVers
- Participa (como NosVers) en 5-10 grupos de jardinage France
- Detecta preguntas en grupos → África responde como experta → visibilidad orgánica
- Crea eventos para los Ateliers Sol Vivant
- Gestiona reviews y comentarios

**Grupos objetivo:**
- Jardinage biologique France (grupos grandes)
- Permaculture Dordogne/Périgord (local)
- Maraîchage paysan
- Compostage et lombricompostage

**Cron:** `0 11 * * *` (cada día 11h)

---

### AGT-10 · Community Manager
**Misión:** Gestionar la comunidad activa — responder comentarios, DMs, emails.

**Canales:**
- Instagram DMs + comentarios
- Facebook comentarios + mensajes
- Email contact@nosvers.com
- Comentarios del blog
- Mensajes Club Sol Vivant Telegram

**Reglas:**
- Respuestas en francés, voz de África
- Preguntas técnicas → responde con conocimiento de la vault
- Consultas de compra → redirige al producto correcto
- Preguntas complejas → "Je vais en parler avec África et je reviens"
- Escala a Angel/África si es sensible

**Cron:** `0 */4 * * *` (cada 4 horas)

---

### AGT-11 · Analytics & Reporting
**Misión:** Recoger métricas de todos los canales y generar insights accionables.

**Métricas que rastrea:**
- Instagram: reach, engagement, followers, clics en bio
- YouTube: views, subscribers, watch time
- Facebook: alcance, engagement, visitas a grupos
- Blog: tráfico orgánico, keywords posicionadas, tiempo en página
- WooCommerce: ventas, productos más vistos, abandono carrito
- Club: nuevos inscritos, churn, engagement PDF

**Output:**
- `analytics/informe-semanal.md` — viernes 18h → lo ve Angel
- `analytics/top-content.md` — qué está funcionando mejor
- `analytics/kpis.md` — actualizado cada lunes

**Cron:** `0 18 * * 5` (viernes 18h)

---

## TABLA RESUMEN — PLANTILLA COMPLETA v2

| Agente | Misión | Cron | Prioridad |
|---|---|---|---|
| AGT-00 Intelligence | Scraping ideas + tendencias web | 6h diario | ALTA |
| AGT-01 Visual | Fotos → visuels para todos los canales | Manual/trigger | ALTA |
| AGT-02 Instagram v2 | Feed + Stories + Reels + colaboraciones | Dom 10h | CRÍTICA |
| AGT-04 SEO Blog | Artículos WordPress optimizados | Lun 7h | ALTA |
| AGT-05 África Link | Conocimiento África → PDFs Club | Cada 6h | CRÍTICA |
| AGT-06 Infoproduct | PDFs + Lemon Squeezy + entrega | Bajo demanda | MEDIA |
| AGT-07 YouTube | Guiones + SEO + publicación | Mar 10h | ALTA |
| AGT-08 Facebook | Página + grupos + eventos | 11h diario | ALTA |
| AGT-09 Content Director | Brief semanal para todos los canales | Dom 9h | CRÍTICA |
| AGT-10 Community | Responder comentarios todos los canales | Cada 4h | MEDIA |
| AGT-11 Analytics | Métricas + informes semanales | Vie 18h | ALTA |
| Orchestrator | Coordinación + alertas | Cada hora | CRÍTICA |

---

## FLUJO SEMANAL AUTOMATIZADO

```
DOMINGO
  9:00 → AGT-09 Content Director lee intelligence + genera brief semanal
  10:00 → AGT-02 Instagram genera 5 posts basados en el brief
  10:30 → AGT-07 YouTube genera guión + descripción semanal

LUNES
  6:00 → AGT-00 Intelligence hace scraping
  7:00 → AGT-04 SEO genera artículo blog
  11:00 → AGT-08 Facebook publica adaptación del post de Instagram

MARTES
  18:00 → YouTube publica (mejor día para jardinage)

MIÉRCOLES-VIERNES
  AGT-10 Community responde cada 4h
  AGT-08 Facebook participa en grupos

VIERNES
  18:00 → AGT-11 Analytics genera informe semanal → Angel lo lee el fin de semana
```

---

## FASES DE IMPLEMENTACIÓN

### FASE 1 — Ya hecho / en marcha
AGT-02 Instagram, AGT-04 SEO, AGT-05 África, Orchestrator

### FASE 2 — Próximas 2 semanas (Code)
AGT-00 Intelligence, AGT-09 Content Director, AGT-07 YouTube

### FASE 3 — Mes 2
AGT-08 Facebook, AGT-10 Community, AGT-11 Analytics

### FASE 4 — Mes 3
Integración completa + optimización basada en datos reales

---

## KPIs POR CANAL (objetivos M6)

| Canal | M1 | M3 | M6 |
|---|---|---|---|
| Instagram seguidores | 100 | 500 | 2.000 |
| YouTube suscriptores | 50 | 200 | 800 |
| Facebook página fans | 200 | 800 | 3.000 |
| Blog visitas/mes | 200 | 800 | 3.000 |
| Club Sol Vivant | 20 | 50 | 100 |
| Ventas productos | 300€ | 800€ | 2.500€ |
