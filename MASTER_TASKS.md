# MASTER_TASKS.md — NosVers · Todo en uno
> Para Claude Code — leer completo antes de empezar
> Autodeploy activo en Hostinger — cada push se despliega automáticamente
> Hacer push a GitHub después de CADA tarea completada

---

## REGLAS DE TRABAJO

1. **Push después de cada tarea** — el autodeploy de Hostinger lo despliega solo
2. **Archivos frontend** → repo GitHub (se despliegan via autodeploy a Hostinger)
3. **Agentes Python** → repo GitHub + copiar al VPS `/home/nosvers/agents/`
4. **config.php** → NUNCA al repo. Solo en servidores
5. **Actualizar HANDOFF.md** al terminar cada bloque

---

## BLOQUE 1 — UI COMPLETA (index.html)

### 1.1 — Vista Ángel: HQ con todos los agentes

Modificar `index.html` para que al login como "angel" muestre el HQ completo como pantalla principal.

**Pantalla principal Angel (sec-hq) — crear nueva sección:**

```html
<div class="section" id="sec-hq">
  <!-- Header HQ -->
  <div style="background:#0E0F0A;margin:-1rem -1rem 1rem;padding:16px 18px 14px;border-radius:0 0 16px 16px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
      <div style="width:30px;height:30px;background:#3D6B20;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px">🌿</div>
      <div style="flex:1">
        <div style="font-size:13px;color:#fdfaf4;font-weight:600">NosVers HQ</div>
        <div style="font-size:9px;color:rgba(253,250,244,.3)">Centro de Operaciones</div>
      </div>
      <div style="display:flex;align-items:center;gap:4px">
        <div style="width:5px;height:5px;background:#7AB648;border-radius:50%;animation:pulse 2s infinite"></div>
        <span style="font-size:9px;color:#7AB648">online</span>
      </div>
    </div>
    <!-- Métricas -->
    <div style="display:flex;gap:6px">
      <div style="flex:1;background:#1C1E14;border-radius:8px;padding:6px 8px;border:0.5px solid rgba(255,255,255,.06)">
        <div id="hq-activos" style="font-size:14px;color:#7AB648;font-weight:600">7</div>
        <div style="font-size:9px;color:rgba(255,255,255,.3)">Agentes</div>
      </div>
      <div style="flex:1;background:#1C1E14;border-radius:8px;padding:6px 8px;border:0.5px solid rgba(255,255,255,.06)">
        <div id="hq-pendientes" style="font-size:14px;color:#E8A020;font-weight:600">2</div>
        <div style="font-size:9px;color:rgba(255,255,255,.3)">Pendientes</div>
      </div>
      <div style="flex:1;background:#1C1E14;border-radius:8px;padding:6px 8px;border:0.5px solid rgba(255,255,255,.06)">
        <div id="hq-vault" style="font-size:14px;color:#fdfaf4;font-weight:600">13</div>
        <div style="font-size:9px;color:rgba(255,255,255,.3)">Vault</div>
      </div>
    </div>
  </div>

  <!-- Chat Director Ejecutivo -->
  <div style="margin-bottom:14px">
    <div id="hq-chat-msgs" style="min-height:60px;max-height:220px;overflow-y:auto;display:flex;flex-direction:column;gap:7px;margin-bottom:8px;scroll-behavior:smooth"></div>
    <div style="display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;margin-bottom:8px">
      <button onclick="hqChatGo('¿Qué hay pendiente?')" style="white-space:nowrap;padding:4px 10px;border-radius:12px;border:1px solid var(--border);background:white;font-size:11px;color:var(--texte-doux);cursor:pointer;font-family:inherit;flex-shrink:0">¿Pendiente?</button>
      <button onclick="hqChatGo('Estado de los animales')" style="white-space:nowrap;padding:4px 10px;border-radius:12px;border:1px solid var(--border);background:white;font-size:11px;color:var(--texte-doux);cursor:pointer;font-family:inherit;flex-shrink:0">Animales</button>
      <button onclick="hqChatGo('Genera posts Instagram esta semana')" style="white-space:nowrap;padding:4px 10px;border-radius:12px;border:1px solid var(--border);background:white;font-size:11px;color:var(--texte-doux);cursor:pointer;font-family:inherit;flex-shrink:0">Posts</button>
      <button onclick="hqChatGo('¿Cómo va el Club Sol Vivant?')" style="white-space:nowrap;padding:4px 10px;border-radius:12px;border:1px solid var(--border);background:white;font-size:11px;color:var(--texte-doux);cursor:pointer;font-family:inherit;flex-shrink:0">Club</button>
    </div>
    <div style="display:flex;gap:6px;align-items:flex-end;background:white;border-radius:18px;border:1px solid var(--border);padding:6px 6px 6px 12px">
      <textarea id="hq-chat-inp" rows="1"
        style="flex:1;border:none;outline:none;resize:none;font-family:inherit;font-size:13px;color:var(--texte);background:transparent;line-height:1.5;max-height:80px;min-height:18px;padding:2px 0"
        placeholder="Pregunta, ordena, consulta..."
        onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();hqChatSend()}"
        oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,80)+'px'"></textarea>
      <button onclick="hqChatSend()" style="width:32px;height:32px;background:#3D6B20;border:none;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>

  <!-- Grid de agentes -->
  <div style="display:flex;flex-direction:column;gap:6px" id="hq-agents-grid">
    <!-- Generado por hqRenderAgents() -->
  </div>
</div>
```

**Panel lateral de agente (añadir al body):**

```html
<div id="agent-panel-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:200;backdrop-filter:blur(3px)" onclick="if(event.target===this)closeAgentPanel()">
  <div id="agent-panel" style="position:absolute;right:0;top:0;bottom:0;width:min(90vw,420px);background:#0E0F0A;display:flex;flex-direction:column">
    <div style="padding:14px 16px 12px;border-bottom:0.5px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:10px;flex-shrink:0">
      <div id="ap-icon" style="width:32px;height:32px;border-radius:8px;background:rgba(90,138,50,.15);display:flex;align-items:center;justify-content:center;font-size:15px">🤖</div>
      <div style="flex:1">
        <div id="ap-name" style="font-size:13px;color:#fdfaf4;font-weight:600">Agente</div>
        <div id="ap-sub" style="font-size:10px;color:rgba(255,255,255,.35)">NosVers</div>
      </div>
      <button onclick="closeAgentPanel()" style="width:28px;height:28px;border-radius:50%;border:0.5px solid rgba(255,255,255,.1);background:transparent;color:rgba(255,255,255,.4);cursor:pointer;font-size:14px">✕</button>
    </div>
    <div id="ap-msgs" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;scroll-behavior:smooth"></div>
    <!-- Subida de foto en panel agente -->
    <div id="ap-photo-bar" style="display:none;padding:6px 12px;background:rgba(255,255,255,.04);border-top:0.5px solid rgba(255,255,255,.06);align-items:center;gap:8px">
      <img id="ap-photo-thumb" style="width:36px;height:36px;border-radius:6px;object-fit:cover" src="" alt="">
      <span id="ap-photo-name" style="font-size:11px;color:rgba(255,255,255,.4);flex:1">Foto lista</span>
      <button onclick="clearAgentPhoto()" style="background:transparent;border:none;color:rgba(255,255,255,.4);cursor:pointer;font-size:14px">✕</button>
    </div>
    <div style="padding:8px 12px 14px;border-top:0.5px solid rgba(255,255,255,.08);flex-shrink:0">
      <div style="display:flex;gap:6px;margin-bottom:6px">
        <button id="ap-photo-btn" onclick="document.getElementById('ap-file-input').click()" style="display:none;padding:5px 10px;border-radius:8px;border:0.5px solid rgba(255,255,255,.12);background:transparent;color:rgba(255,255,255,.5);font-size:11px;cursor:pointer;font-family:inherit">📎 Foto</button>
        <input type="file" id="ap-file-input" accept="image/*" capture="environment" style="display:none" onchange="onAgentPhotoSelect(event)">
      </div>
      <div style="display:flex;gap:6px;align-items:flex-end;background:#1C1E14;border-radius:16px;border:0.5px solid rgba(255,255,255,.1);padding:6px 6px 6px 12px">
        <textarea id="ap-inp" rows="1"
          style="flex:1;border:none;outline:none;resize:none;font-family:inherit;font-size:13px;color:#fdfaf4;background:transparent;line-height:1.5;max-height:80px;min-height:18px;padding:2px 0"
          placeholder="Habla con este agente..."
          onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();agentPanelSend()}"
          oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,80)+'px'"></textarea>
        <button onclick="agentPanelSend()" id="ap-send" style="width:30px;height:30px;background:#3D6B20;border:none;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
  </div>
</div>
```

**JavaScript a añadir antes del cierre del último `</script>`:**

```javascript
// ══ HQ ANGEL ══════════════════════════════════════════════════

const HQ_AGENTS = [
  { id:'orchestrator', name:'Orchestrator', icon:'🎯', color:'#3D6B20', borderColor:'rgba(90,138,50,.3)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Verificando agentes cada hora', cron:'Cada hora', photo:false,
    ctx:'Eres el Orchestrator de NosVers. Coordinador central de todos los agentes. Ferme: Neuvic, Dordogne. CEO: Angel. Responde en español, directo.' },
  { id:'agt00_intelligence', name:'AGT-00 Intelligence', icon:'🔎', color:'#0F6E56', borderColor:'rgba(29,158,117,.3)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Scraping blogs · Google Trends · Foros', cron:'6h diario', photo:false,
    ctx:'Eres AGT-00 Intelligence de NosVers. Monitorizas blogs franceses de jardinage, Google Trends sobre lombricompost y suelo vivo, foros y grupos Facebook de jardinage France. Generas ideas de contenido semanales. Responde en español.' },
  { id:'agt01_visual', name:'AGT-01 Visual', icon:'📷', color:'#854F0B', borderColor:'rgba(196,130,10,.3)',
    status:'waiting', statusLabel:'Esperando', statusColor:'#E8A020',
    last:'Esperando fotos de África', cron:'Bajo demanda', photo:true,
    ctx:'Eres AGT-01 Visual Director de NosVers. Procesas fotos brutas de África siguiendo la identidad visual: paleta #FEFAF4 + #5A7A2E, estilo editorial organique. Protocolo: evaluación → recadrage → exposición → balance blancs → saturación → contraste → viñeta → JPEG 90%. Si recibes una foto, analízala y sugiere cómo procesarla.' },
  { id:'agt02_instagram', name:'AGT-02 Instagram', icon:'📱', color:'#993556', borderColor:'rgba(212,83,126,.3)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'5 posts S1 listos · esperando fotos', cron:'Dom 10h', photo:true, badge:1,
    ctx:'Eres AGT-02 Instagram Manager de NosVers. Generas 5 posts/semana para @nosvers.ferme. Calendario: L(ferme 18h) X(educatif 19h) J(reel 18h) V(África 18h) D(Club 11h). Voz: 80% educatif, 20% produit. Idioma: francés siempre. CTA único: lien en bio. Si recibes foto, genera el caption completo con hashtags.' },
  { id:'agt04_seo', name:'AGT-04 SEO Blog', icon:'🔍', color:'#27500A', borderColor:'rgba(99,153,34,.2)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Post ID 458 publicado', cron:'Lun 7h', photo:true,
    ctx:'Eres AGT-04 SEO Manager de NosVers. Generas artículos blog semanales optimizados. Keywords: lombricompost dordogne, ferme lombricole france, sol vivant jardin. Estructura: 800-1500 palabras, H2s claros, meta 155 chars, CTA al Club o producto. Si recibes foto, sugiere cómo incluirla en el artículo.' },
  { id:'agt05_africa', name:'AGT-05 África', icon:'🌺', color:'#3C3489', borderColor:'rgba(127,119,221,.4)',
    status:'urgent', statusLabel:'¡Acción!', statusColor:'#E24B4A',
    last:'PDF #1 listo · respuestas recibidas', cron:'Cada 6h', photo:true, badge:'!',
    ctx:'Eres AGT-05 África Link de NosVers. Procesas el conocimiento de África Sánchez y lo estructuras para el Club Sol Vivant. Sus respuestas ya están en la vault. PDF #1 "Comprendre votre sol en 5 observations" generado. Si recibes foto de África, analízala y añádela como observación al conocimiento.' },
  { id:'agt07_youtube', name:'AGT-07 YouTube', icon:'▶', color:'#712B13', borderColor:'rgba(216,90,48,.3)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Generando guiones sin voz', cron:'Mar 10h', photo:true,
    ctx:'Eres AGT-07 YouTube Manager de NosVers. Generas guiones para vídeos sin voz de África: timelapse lombricompost, manos trabajando + texto, proceso LombriThé, antes/después bancales. Formato: 60-90s con descripción SEO completa + tags + thumbnail. Si recibes foto/vídeo, sugiere cómo usarla en el canal.' },
  { id:'agt08_facebook', name:'AGT-08 Facebook', icon:'📘', color:'#0C447C', borderColor:'rgba(55,138,221,.3)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Adaptando contenido Instagram', cron:'11h diario', photo:false,
    ctx:'Eres AGT-08 Facebook Manager de NosVers. Gestionas la página NosVers y participas en grupos de jardinage France. Adaptas el contenido de Instagram para Facebook (audiencia 40-60 años). Participas en: Jardinage biologique France, Permaculture Dordogne, Compostage et lombricompostage.' },
  { id:'agt09_content', name:'AGT-09 Content Director', icon:'🎬', color:'#534AB7', borderColor:'rgba(127,119,221,.35)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Brief semanal generado', cron:'Dom 9h', photo:false,
    ctx:'Eres AGT-09 Content Director de NosVers. Lees la intelligence de AGT-00 y generas el brief semanal para todos los canales. Principio: un tema, cuatro formatos (Instagram + Blog + YouTube + Facebook). Mantienes coherencia de mensaje y calendario a 4 semanas.' },
  { id:'agt10_community', name:'AGT-10 Community', icon:'💬', color:'#72243E', borderColor:'rgba(212,83,126,.25)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Monitorizando comentarios', cron:'Cada 4h', photo:false,
    ctx:'Eres AGT-10 Community Manager de NosVers. Respondes comentarios en Instagram, Facebook, blog y emails con la voz de África. Francés siempre, tono cálido y experto. Para preguntas técnicas complejas: "Je vais en parler avec África et je reviens".' },
  { id:'agt11_analytics', name:'AGT-11 Analytics', icon:'📊', color:'#185FA5', borderColor:'rgba(55,138,221,.25)',
    status:'active', statusLabel:'Activo', statusColor:'#7AB648',
    last:'Informe viernes pendiente', cron:'Vie 18h', photo:false,
    ctx:'Eres AGT-11 Analytics de NosVers. Rastreas métricas de Instagram, YouTube, Facebook, blog y WooCommerce. Generas informe semanal los viernes con insights accionables para Angel. KPIs: M3→600€/mes, M6→2000€/mes, Club M1→20 membres.' },
  { id:'agt06_infoproduct', name:'AGT-06 Infoproduct', icon:'📄', color:'#444441', borderColor:'rgba(255,255,255,.06)',
    status:'waiting', statusLabel:'Fase 1', statusColor:'rgba(255,255,255,.3)',
    last:'Activar cuando PDF #1 aprobado', cron:'Bajo demanda', photo:false, inactive:true,
    ctx:'Eres AGT-06 Infoproduct de NosVers. Cuando se active: maquetas PDFs + configuras Lemon Squeezy + entrega automática. Productos: 27€, 37€, 47€.' }
];

let hqChatHist = [], apHist = [], apBusy = false, currentAgent = null, apPhoto = null;

const HQ_CTX = `Eres el Director Ejecutivo de NosVers, ferme lombricole en Neuvic, Dordogne. Angel es el CEO. Responde en español, directo. Estado: 11 agentes activos, vault 13 archivos, MCP conectado. Productos: Extrait Vivant 45€, Engrais Vert 9.90€, Atelier 85€, Club Sol Vivant 15€/mes. Ferme: gallinas, canards, lapins, brebis, lombricultivo.`;

function hqRenderAgents() {
  const g = document.getElementById('hq-agents-grid');
  if (!g) return;
  g.innerHTML = HQ_AGENTS.map(a => {
    const bc = a.urgent ? 'rgba(196,74,74,.4)' : (a.inactive ? 'rgba(255,255,255,.05)' : a.borderColor);
    const badge = a.badge ? `<div style="background:#E24B4A;color:white;font-size:9px;font-weight:600;width:15px;height:15px;border-radius:50%;display:flex;align-items:center;justify-content:center;position:absolute;top:8px;right:8px">${a.badge}</div>` : '';
    return `
    <div onclick="openAgent('${a.id}')" style="background:#1C1E14;border-radius:10px;border:0.5px solid ${bc};cursor:pointer;position:relative;${a.inactive?'opacity:.5':''}">
      ${badge}
      <div style="padding:8px 10px;display:flex;align-items:center;gap:8px">
        <div style="width:28px;height:28px;background:rgba(255,255,255,.06);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0">${a.icon}</div>
        <div style="flex:1;min-width:0">
          <div style="font-size:11px;color:#fdfaf4;font-weight:600">${a.name}</div>
          <div style="font-size:10px;color:rgba(255,255,255,.35);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${a.last}</div>
        </div>
        <div style="display:flex;align-items:center;gap:3px;background:rgba(255,255,255,.06);border-radius:8px;padding:2px 7px;flex-shrink:0">
          <div style="width:4px;height:4px;background:${a.statusColor};border-radius:50%"></div>
          <span style="font-size:9px;color:${a.statusColor}">${a.statusLabel}</span>
        </div>
      </div>
      <div style="padding:0 10px 7px;display:flex;gap:5px">
        <span style="font-size:9px;color:rgba(255,255,255,.25);background:rgba(255,255,255,.04);border-radius:4px;padding:2px 6px">⏱ ${a.cron}</span>
        <span style="font-size:10px;color:#7AB648;margin-left:auto;padding:2px 6px">Hablar →</span>
      </div>
    </div>`;
  }).join('');
}

function hqAddMsg(role, text, container='hq-chat-msgs') {
  const c = document.getElementById(container);
  if (!c) return;
  const d = document.createElement('div');
  const isUser = role === 'user';
  d.style.cssText = 'display:flex;flex-direction:column;max-width:88%;' + (isUser ? 'align-self:flex-end;align-items:flex-end' : 'align-self:flex-start;align-items:flex-start');
  const fmt = text.replace(/\*\*(.*?)\*\*/g,'<b>$1</b>').replace(/\n/g,'<br>');
  const bg = isUser
    ? (container==='ap-msgs' ? 'background:#2D4A18' : 'background:#2D5018')
    : (container==='ap-msgs' ? 'background:#22251a;border:0.5px solid rgba(255,255,255,.08)' : 'background:white;color:#1c1510;border:1px solid #e0d8cc');
  const tc = (isUser || container==='ap-msgs') ? 'color:#fdfaf4' : 'color:#1c1510';
  d.innerHTML = `<div style="padding:8px 11px;border-radius:14px 14px ${isUser?'3px 14px':'14px 3px'};font-size:12px;line-height:1.6;word-break:break-word;${bg};${tc}">${fmt}</div>`;
  c.appendChild(d); c.scrollTop = c.scrollHeight;
}

function hqTyping(container) {
  const c = document.getElementById(container);
  const ty = document.createElement('div');
  ty.id = container+'-ty'; ty.style.cssText = 'align-self:flex-start';
  const bg = container==='ap-msgs' ? 'background:#22251a;border:0.5px solid rgba(255,255,255,.08)' : 'background:white;border:1px solid #e0d8cc;color:#1c1510';
  ty.innerHTML = `<div style="${bg};border-radius:14px;padding:9px 12px;display:flex;gap:3px"><div style="width:5px;height:5px;background:currentColor;border-radius:50%;opacity:.5;animation:bo .8s infinite"></div><div style="width:5px;height:5px;background:currentColor;border-radius:50%;opacity:.5;animation:bo .8s .15s infinite"></div><div style="width:5px;height:5px;background:currentColor;border-radius:50%;opacity:.5;animation:bo .8s .3s infinite"></div></div>`;
  c && c.appendChild(ty) && (c.scrollTop = c.scrollHeight);
}
function rmTyping(id) { document.getElementById(id)?.remove(); }

async function hqChatSend() {
  const inp = document.getElementById('hq-chat-inp');
  const txt = inp.value.trim(); if (!txt) return;
  inp.value = ''; inp.style.height = 'auto';
  await hqChatGo(txt);
}

async function hqChatGo(txt) {
  hqAddMsg('user', txt);
  hqChatHist.push({role:'user',content:txt});
  hqTyping('hq-chat-msgs');
  try {
    const res = await fetch(API_URL+'?action=agente',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({system:HQ_CTX,user:txt,messages:hqChatHist.slice(-8)})});
    rmTyping('hq-chat-msgs-ty');
    const data = await res.json();
    const reply = data.content?.find(b=>b.type==='text')?.text || '⚠️ '+(data.error||'Sin respuesta');
    hqAddMsg('ai', reply);
    hqChatHist.push({role:'assistant',content:reply});
  } catch(e) { rmTyping('hq-chat-msgs-ty'); hqAddMsg('ai','⚠️ '+e.message); }
}

function openAgent(id) {
  currentAgent = HQ_AGENTS.find(a=>a.id===id);
  if (!currentAgent) return;
  apHist = []; apPhoto = null;
  document.getElementById('ap-icon').textContent = currentAgent.icon;
  document.getElementById('ap-name').textContent = currentAgent.name;
  document.getElementById('ap-sub').textContent = currentAgent.cron + ' · ' + currentAgent.last.slice(0,40);
  document.getElementById('ap-msgs').innerHTML = '';
  document.getElementById('ap-photo-btn').style.display = currentAgent.photo ? 'inline-block' : 'none';
  document.getElementById('ap-photo-bar').style.display = 'none';
  document.getElementById('agent-panel-overlay').style.display = 'flex';
  setTimeout(()=>document.getElementById('ap-inp').focus(),300);
  // Mensaje de bienvenida
  const welcome = {
    orchestrator: 'Hola Angel 🎯 Sistema activo. 7 agentes corriendo, vault con 13 archivos. ¿Qué necesitas?',
    agt00_intelligence: 'Hola 🔎 Monitorizo blogs y tendencias de jardinage en Francia cada mañana. ¿Quieres las ideas de esta semana?',
    agt01_visual: 'Hola 📷 Listo para procesar las fotos de África. Envíame una foto y te digo cómo procesarla para Instagram.',
    agt02_instagram: 'Hola 📱 5 posts S1 generados, esperando fotos de África. ¿Quieres verlos o genero nuevos?',
    agt04_seo: 'Hola 🔍 Post ID 458 publicado (Texas A&M). Próximo artículo lunes 7h. ¿Quieres ver el tema propuesto?',
    agt05_africa: '🔔 **Acción necesaria** — África respondió las 5 preguntas. PDF #1 generado. ¿Lo revisamos?',
    agt07_youtube: 'Hola ▶ Listo para generar guiones sin voz para África. ¿Qué proceso de la ferme quieres que sea el primer vídeo?',
    agt08_facebook: 'Hola 📘 Adaptando el contenido de Instagram para Facebook. Audiencia objetivo: jardineros 40-60 años Francia.',
    agt09_content: 'Hola 🎬 Brief semanal generado. Un tema, cuatro formatos. ¿Lo revisamos juntos?',
    agt10_community: 'Hola 💬 Monitorizando comentarios en todos los canales. Sin nuevas interacciones que escalar.',
    agt11_analytics: 'Hola 📊 Informe semanal pendiente para este viernes. ¿Quieres ver el resumen de métricas actuales?',
    agt06_infoproduct: 'Hola 📄 En espera de activación. Se activa cuando PDF #1 sea aprobado por Angel.'
  };
  setTimeout(()=>hqAddMsg('ai', welcome[id] || 'Hola, soy '+currentAgent.name+'. ¿En qué puedo ayudarte?', 'ap-msgs'), 200);
}

function closeAgentPanel() {
  document.getElementById('agent-panel-overlay').style.display = 'none';
  currentAgent = null; apHist = []; apPhoto = null;
  document.getElementById('ap-photo-bar').style.display = 'none';
}

function onAgentPhotoSelect(e) {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    const dataUrl = ev.target.result;
    apPhoto = { base64: dataUrl.split(',')[1], type: file.type, name: file.name };
    document.getElementById('ap-photo-thumb').src = dataUrl;
    document.getElementById('ap-photo-name').textContent = file.name;
    document.getElementById('ap-photo-bar').style.display = 'flex';
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function clearAgentPhoto() {
  apPhoto = null;
  document.getElementById('ap-photo-bar').style.display = 'none';
}

async function agentPanelSend() {
  if (apBusy || !currentAgent) return;
  const inp = document.getElementById('ap-inp');
  const txt = inp.value.trim();
  const photo = apPhoto;
  if (!txt && !photo) return;
  inp.value = ''; inp.style.height = 'auto'; clearAgentPhoto();
  apBusy = true; document.getElementById('ap-send').disabled = true;

  hqAddMsg('user', txt || '(foto adjunta)', 'ap-msgs');
  apHist.push({role:'user', content: txt || 'Analiza esta imagen en el contexto de la ferme NosVers.'});
  hqTyping('ap-msgs');

  try {
    const payload = { system: currentAgent.ctx, user: txt || 'Analiza esta imagen.', messages: apHist.slice(-8) };
    if (photo && photo.type.startsWith('image/')) {
      payload.user_content = [
        { type:'image', source:{ type:'base64', media_type: photo.type, data: photo.base64 } },
        { type:'text', text: txt || 'Analiza esta imagen en el contexto de la ferme NosVers.' }
      ];
    }
    const res = await fetch(API_URL+'?action=agente',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    rmTyping('ap-msgs-ty');
    const data = await res.json();
    const reply = data.content?.find(b=>b.type==='text')?.text || '⚠️ '+(data.error||'');
    hqAddMsg('ai', reply, 'ap-msgs');
    apHist.push({role:'assistant', content:reply});
  } catch(e) { rmTyping('ap-msgs-ty'); hqAddMsg('ai','⚠️ '+e.message,'ap-msgs'); }

  apBusy = false; document.getElementById('ap-send').disabled = false;
  document.getElementById('ap-inp').focus();
}

// ══ VISTA ÁFRICA ══════════════════════════════════════════

const CTX_AFRICA_APP = `Tu es l'assistante personnelle d'África pour la ferme NosVers à Neuvic, Dordogne, France. África gère la ferme : vers, compost, animaux, potager. Réponds TOUJOURS en français. Ton chaleureux, proche, pratique. Si elle envoie une photo → analyse en détail : vers (santé, densité), jardin (plantes, sol), ou Instagram (suggest caption). Aide-la à documenter ses observations pour le Club Sol Vivant. Ne parle jamais de code ou de technique IT.`;

let africaHist = [], africaPhoto = null;

// La sección África debe añadirse al HTML (sec-africa)
// Ver sección 1.2 más abajo para el HTML completo

function africaAddMsg(role, text) {
  const c = document.getElementById('africa-msgs');
  if (!c) return;
  const d = document.createElement('div');
  const isUser = role === 'user';
  d.style.cssText = 'display:flex;flex-direction:column;max-width:88%;' + (isUser?'align-self:flex-end;align-items:flex-end':'align-self:flex-start;align-items:flex-start');
  const fmt = text.replace(/\*\*(.*?)\*\*/g,'<b>$1</b>').replace(/\n/g,'<br>');
  const bg = isUser ? 'background:#7A3A6A;color:white;border-radius:14px 14px 3px 14px' : 'background:white;border:0.5px solid #e0d8cc;color:#1c1510;border-radius:14px 14px 14px 3px';
  d.innerHTML = `<div style="padding:9px 12px;font-size:13px;line-height:1.6;word-break:break-word;${bg}">${fmt}</div>`;
  c.appendChild(d); c.scrollTop = c.scrollHeight;
}

// ══ LOGIN → ROUTING ══════════════════════════════════════

function onLoginSuccess(user, token) {
  localStorage.setItem('nosvers_token', btoa(user + ':' + (user==='angel'?'Angel':'Africa')));
  document.getElementById('loginScreen').style.display = 'none';
  document.getElementById('userBadge').style.display = 'flex';
  document.getElementById('userBadgeName').textContent = user;

  if (user === 'africa') {
    showAfricaMode();
  } else {
    showAngelHQ();
  }
}

function showAngelHQ() {
  document.querySelector('.nav-tabs').style.display = 'flex';
  goTo('hq');
  hqRenderAgents();
  // Saludo automático
  setTimeout(()=>{
    const h = new Date().getHours();
    const s = h<12?'Buenos días':h<20?'Buenas tardes':'Buenas noches';
    hqAddMsg('ai', s+' Angel 🌿 Sistema activo. ¿Qué necesitas hoy?');
  }, 600);
}

function showAfricaMode() {
  document.querySelector('.nav-tabs').style.display = 'none';
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.getElementById('sec-africa') && document.getElementById('sec-africa').classList.add('active');
  // Saludo África
  setTimeout(()=>{
    const h = new Date().getHours();
    const s = h<12?'Bonjour África':'Bonsoir África';
    africaAddMsg('ai', s+' 🌿 Qu\'est-ce que tu observes aujourd\'hui ?');
  }, 600);
}
```

### 1.2 — Sección África (añadir al HTML, después de sec-hq)

```html
<div class="section" id="sec-africa" style="padding:0">
  <!-- Header África -->
  <div style="background:#f4efe4;padding:12px 16px 10px;border-radius:0 0 16px 16px;margin-bottom:14px">
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:32px;height:32px;background:#7A3A6A;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px">🌺</div>
      <div style="flex:1">
        <div style="font-size:14px;color:#1c1510;font-weight:600">Hola África</div>
        <div style="font-size:10px;color:rgba(0,0,0,.4)">NosVers · La ferme · Dordogne</div>
      </div>
      <div style="display:flex;align-items:center;gap:4px">
        <div style="width:5px;height:5px;background:#5A8A32;border-radius:50%"></div>
        <span style="font-size:9px;color:#5A8A32">en ligne</span>
      </div>
    </div>
  </div>

  <!-- Accesos rápidos -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">
    <button onclick="document.getElementById('africa-file').click()" style="background:white;border-radius:12px;border:0.5px solid #e0d8cc;padding:12px 8px;text-align:center;cursor:pointer;font-family:inherit">
      <div style="font-size:20px;margin-bottom:4px">📷</div>
      <div style="font-size:12px;color:#1c1510;font-weight:500">Foto del día</div>
      <div style="font-size:10px;color:rgba(0,0,0,.4)">Subir al sistema</div>
    </button>
    <button onclick="africaChatGo('Montre-moi le PDF #1 du Club Sol Vivant')" style="background:white;border-radius:12px;border:0.5px solid #e0d8cc;padding:12px 8px;text-align:center;cursor:pointer;font-family:inherit">
      <div style="font-size:20px;margin-bottom:4px">📄</div>
      <div style="font-size:12px;color:#1c1510;font-weight:500">Mon PDF</div>
      <div style="font-size:10px;color:rgba(0,0,0,.4)">Club Sol Vivant</div>
    </button>
  </div>
  <input type="file" id="africa-file" accept="image/*" capture="environment" style="display:none" onchange="onAfricaPhotoSelect(event)">

  <!-- Preview foto África -->
  <div id="africa-photo-bar" style="display:none;background:#f0ead8;border-radius:10px;padding:8px 12px;margin-bottom:8px;align-items:center;gap:8px">
    <img id="africa-photo-thumb" style="width:40px;height:40px;border-radius:8px;object-fit:cover" src="" alt="">
    <span id="africa-photo-name" style="font-size:11px;color:rgba(0,0,0,.4);flex:1"></span>
    <button onclick="clearAfricaPhoto()" style="background:transparent;border:none;color:rgba(0,0,0,.4);cursor:pointer;font-size:15px">✕</button>
  </div>

  <!-- Chat África -->
  <div id="africa-msgs" style="min-height:160px;max-height:320px;overflow-y:auto;display:flex;flex-direction:column;gap:8px;margin-bottom:10px;scroll-behavior:smooth"></div>

  <!-- Input África -->
  <div style="display:flex;gap:7px;align-items:flex-end;background:white;border-radius:20px;border:1px solid #e0d8cc;padding:7px 7px 7px 14px">
    <textarea id="africa-inp" rows="1"
      style="flex:1;border:none;outline:none;resize:none;font-family:inherit;font-size:14px;color:#1c1510;background:transparent;line-height:1.5;max-height:100px;min-height:20px;padding:2px 0"
      placeholder="Écris ou envoie une photo..."
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();africaChatSend()}"
      oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,100)+'px'"></textarea>
    <button onclick="africaChatSend()" style="width:34px;height:34px;background:#7A3A6A;border:none;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;color:white;flex-shrink:0">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
    </button>
  </div>
</div>
```

**JavaScript África (añadir al bloque JS):**

```javascript
function onAfricaPhotoSelect(e) {
  const file = e.target.files[0]; if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    africaPhoto = { base64: ev.target.result.split(',')[1], type: file.type, name: file.name };
    document.getElementById('africa-photo-thumb').src = ev.target.result;
    document.getElementById('africa-photo-name').textContent = file.name;
    document.getElementById('africa-photo-bar').style.display = 'flex';
  };
  reader.readAsDataURL(file);
  e.target.value = '';
}

function clearAfricaPhoto() {
  africaPhoto = null;
  document.getElementById('africa-photo-bar').style.display = 'none';
}

async function africaChatSend() {
  const inp = document.getElementById('africa-inp');
  const txt = inp.value.trim(); const photo = africaPhoto;
  if (!txt && !photo) return;
  inp.value = ''; inp.style.height = 'auto'; clearAfricaPhoto();
  africaAddMsg('user', txt || '(photo jointe)');
  africaHist.push({role:'user', content: txt || 'Analyse cette image.'});
  // typing
  const c = document.getElementById('africa-msgs');
  const ty = document.createElement('div');
  ty.id='africa-ty';ty.style.cssText='align-self:flex-start';
  ty.innerHTML='<div style="background:white;border:0.5px solid #e0d8cc;border-radius:14px;padding:10px 13px;display:flex;gap:3px"><div style="width:5px;height:5px;background:#aaa;border-radius:50%;animation:bo .8s infinite"></div><div style="width:5px;height:5px;background:#aaa;border-radius:50%;animation:bo .8s .15s infinite"></div><div style="width:5px;height:5px;background:#aaa;border-radius:50%;animation:bo .8s .3s infinite"></div></div>';
  c.appendChild(ty); c.scrollTop=c.scrollHeight;
  try {
    const payload = { system: CTX_AFRICA_APP, user: txt || 'Analyse cette image de la ferme.', messages: africaHist.slice(-8) };
    if (photo && photo.type.startsWith('image/')) {
      payload.user_content = [
        { type:'image', source:{ type:'base64', media_type: photo.type, data: photo.base64 } },
        { type:'text', text: txt || 'Analyse cette image de la ferme NosVers.' }
      ];
    }
    const res = await fetch(API_URL+'?action=agente',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    document.getElementById('africa-ty')?.remove();
    const data = await res.json();
    const reply = data.content?.find(b=>b.type==='text')?.text || '⚠️ Erreur de connexion';
    africaAddMsg('ai', reply);
    africaHist.push({role:'assistant', content:reply});
    // Guardar observación en vault si hay foto
    if (photo) saveAfricaObservation(txt, reply);
  } catch(e) { document.getElementById('africa-ty')?.remove(); africaAddMsg('ai','⚠️ Connexion impossible'); }
}

async function africaChatGo(txt) {
  document.getElementById('africa-inp').value = txt;
  await africaChatSend();
}

async function saveAfricaObservation(pregunta, respuesta) {
  const fecha = new Date().toISOString().split('T')[0];
  const entry = `\n\n## ${fecha} — Observación África\n**Consulta:** ${pregunta||'(foto)'}\n**Análisis:** ${respuesta}`;
  try {
    await fetch(API_URL+'?action=vault_write', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ category:'contexto', filename:'africa-conocimiento', content: entry, mode:'append' })
    });
  } catch(e) {}
}
```

### 1.3 — Modificar el login para hacer el routing

Buscar en index.html la función de login existente y añadir:

```javascript
// En la función que procesa el login exitoso, añadir al final:
// Si es Africa → showAfricaMode()
// Si es Angel/Claude → showAngelHQ()
// El tab HQ debe añadirse a la nav:
// <button class="nav-tab active" onclick="goTo('hq')">🏠 HQ</button>
```

---

## BLOQUE 2 — NUEVOS AGENTES PYTHON (VPS + repo)

Crear estos archivos en `/home/nosvers/agents/` Y en el repo:

### agents/agt00_intelligence.py

```python
#!/usr/bin/env python3
"""
AGT-00 · Intelligence Collector
Misión: Scraping de blogs + Google Trends + foros jardinage France
Genera ideas diarias de contenido para el Content Director
Cron: 0 6 * * *
"""
import os, json, requests, feedparser
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

# Fuentes RSS de jardinage France
RSS_FEEDS = [
    'https://www.rustica.fr/feed',
    'https://www.jardiner-malin.fr/feed',
    'https://permaculturedesign.fr/feed',
    'https://www.bioalaune.com/feed',
]

KEYWORDS = ['lombricompost','sol vivant','permaculture','jardinage bio','compostage','engrais vert']

def fetch_rss_ideas():
    ideas = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                title = entry.get('title','')
                if any(kw in title.lower() for kw in KEYWORDS):
                    ideas.append({'source': feed.feed.get('title',''), 'title': title, 'url': entry.get('link','')})
        except: pass
    return ideas

def generate_content_ideas(raw_ideas):
    if not ANTHROPIC_KEY or not raw_ideas:
        return "Sin ideas esta semana — verificar fuentes RSS"
    
    ideas_text = '\n'.join([f"- {i['title']} ({i['source']})" for i in raw_ideas[:10]])
    
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 800,
        "system": "Eres el Intelligence Collector de NosVers, ferme lombricole en Dordogne. Generas ideas de contenido accionables basadas en tendencias de jardinage en Francia.",
        "messages": [{"role": "user", "content": f"Basándote en estas noticias de jardinage France, genera 5 ideas de contenido específicas para NosVers (lombricompost, suelo vivo, jardinage bio):\n\n{ideas_text}\n\nFormato: idea concreta + canal sugerido (Instagram/Blog/YouTube/Facebook)"}]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','Error generando ideas')

def main():
    print(f"[{datetime.now()}] AGT-00 Intelligence iniciando")
    
    ideas_raw = fetch_rss_ideas()
    ideas_content = generate_content_ideas(ideas_raw)
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    content = f"## {fecha} — Ideas semanales\n\n{ideas_content}\n\n### Fuentes detectadas\n"
    for i in ideas_raw[:5]:
        content += f"- [{i['title']}]({i['url']})\n"
    
    # Guardar en vault
    intel_path = VAULT_PATH / 'intelligence'
    intel_path.mkdir(exist_ok=True)
    ideas_file = intel_path / 'ideas-semaine.md'
    
    with open(ideas_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n---\n{content}")
    
    print(f"[{datetime.now()}] Ideas guardadas en vault/intelligence/ideas-semaine.md")

if __name__ == '__main__':
    main()
```

### agents/agt07_youtube.py

```python
#!/usr/bin/env python3
"""
AGT-07 · YouTube Manager
Misión: Guiones sin voz + SEO + publicación
Cron: 0 10 * * 2 (martes 10h)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
WP_URL = os.getenv('WP_URL','https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER','claude_nosvers')
WP_PASS = os.getenv('WP_PASS','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

SYSTEM_YT = """Eres AGT-07 YouTube Manager de NosVers, ferme lombricole en Dordogne.
Generas guiones para vídeos SIN VOZ de África (texto superposado + imágenes).
Formatos: timelapse lombricompost, proceso LombriThé, antes/después bancales, un día en la ferme.
Duración objetivo: 60-90 segundos.
Siempre incluir: título SEO, descripción optimizada (500 palabras), 15 tags, thumbnail sugerido."""

def generate_script(tema):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 1200,
        "system": SYSTEM_YT,
        "messages": [{"role": "user", "content": f"Genera un guión completo para: {tema}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-07 YouTube iniciando")
    
    # Leer brief semanal
    brief_path = VAULT_PATH / 'operaciones' / 'brief-semanal.md'
    tema = "Le processus du lombricompostage de A à Z"
    if brief_path.exists():
        brief = brief_path.read_text(encoding='utf-8')
        if 'YouTube' in brief:
            lines = [l for l in brief.split('\n') if 'YouTube' in l or 'video' in l.lower()]
            if lines: tema = lines[0].replace('YouTube:', '').strip()
    
    script = generate_script(tema)
    
    # Guardar en vault
    fecha = datetime.now().strftime('%Y-%m-%d')
    yt_path = VAULT_PATH / 'agentes' / 'agt07_youtube'
    yt_path.mkdir(parents=True, exist_ok=True)
    
    with open(yt_path / '_resultado.md', 'w', encoding='utf-8') as f:
        f.write(f"# Guión YouTube — {fecha}\n\n{script}")
    
    print(f"[{datetime.now()}] Guión guardado")

if __name__ == '__main__':
    main()
```

### agents/agt08_facebook.py

```python
#!/usr/bin/env python3
"""
AGT-08 · Facebook Manager  
Misión: Adaptar contenido Instagram para Facebook + grupos
Cron: 0 11 * * * (diario 11h)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

GRUPOS_OBJETIVO = [
    "Jardinage biologique France",
    "Permaculture Dordogne / Périgord", 
    "Compostage et lombricompostage",
    "Maraîchage paysan France"
]

SYSTEM_FB = """Eres AGT-08 Facebook Manager de NosVers.
Adaptas el contenido de Instagram para Facebook (audiencia 40-65 años, jardineros Francia).
Facebook requiere: más texto, más contexto, tono educativo pero accesible.
También generas participaciones orgánicas en grupos de jardinage (como NosVers, experto en suelo vivo).
Idioma: francés siempre."""

def adapt_for_facebook(instagram_post):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 600,
        "system": SYSTEM_FB,
        "messages": [{"role": "user", "content": f"Adapta este post de Instagram para Facebook, haciéndolo más informativo y añadiendo contexto para una audiencia de 40-65 años:\n\n{instagram_post}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-08 Facebook iniciando")
    
    # Leer último post de Instagram
    ig_path = VAULT_PATH / 'agentes' / 'agt02-posts-pendientes.md'
    if not ig_path.exists():
        print("Sin posts Instagram para adaptar")
        return
    
    ig_content = ig_path.read_text(encoding='utf-8')
    fb_post = adapt_for_facebook(ig_content[:800])
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    fb_path = VAULT_PATH / 'agentes' / 'agt08_facebook'
    fb_path.mkdir(parents=True, exist_ok=True)
    
    with open(fb_path / '_resultado.md', 'w', encoding='utf-8') as f:
        f.write(f"# Post Facebook — {fecha}\n\n{fb_post}\n\n## Grupos para compartir\n")
        for g in GRUPOS_OBJETIVO:
            f.write(f"- {g}\n")
    
    print(f"[{datetime.now()}] Post Facebook generado")

if __name__ == '__main__':
    main()
```

### agents/agt09_content_director.py

```python
#!/usr/bin/env python3
"""
AGT-09 · Content Director
Misión: Brief semanal para todos los canales — un tema, cuatro formatos
Cron: 0 9 * * 0 (domingos 9h, antes que AGT-02)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

SYSTEM_CD = """Eres AGT-09 Content Director de NosVers, ferme lombricole en Dordogne.
Generas el brief semanal de contenido para todos los canales.
Principio fundamental: UN TEMA → CUATRO FORMATOS (Instagram + Blog/SEO + YouTube + Facebook).
Lees las ideas de Intelligence (vault/intelligence/) y el conocimiento de África (vault/contexto/africa-conocimiento.md).
El tema debe ser estacional, relevante, y basado en el conocimiento real de África.
Output: brief completo con instrucciones específicas para cada agente."""

def generate_brief():
    # Leer intelligence y conocimiento de África
    intel_path = VAULT_PATH / 'intelligence' / 'ideas-semaine.md'
    africa_path = VAULT_PATH / 'contexto' / 'africa-conocimiento.md'
    
    intel = intel_path.read_text(encoding='utf-8')[-800:] if intel_path.exists() else ""
    africa = africa_path.read_text(encoding='utf-8')[-800:] if africa_path.exists() else ""
    
    semana = datetime.now().strftime('%Y semaine %W')
    
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 1500,
        "system": SYSTEM_CD,
        "messages": [{"role": "user", "content": f"Genera el brief semanal para {semana}.\n\nInteligence esta semana:\n{intel}\n\nConocimiento de África:\n{africa}\n\nIncluye: tema principal, instrucciones para Instagram (5 posts), Blog (1 artículo), YouTube (1 guión), Facebook (1 post + 2 participaciones en grupos)."}]
    }
    
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=45)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-09 Content Director iniciando")
    
    brief = generate_brief()
    fecha = datetime.now().strftime('%Y-%m-%d')
    
    brief_path = VAULT_PATH / 'operaciones' / 'brief-semanal.md'
    brief_path.write_text(f"# Brief Semanal — {fecha}\n\n{brief}", encoding='utf-8')
    
    print(f"[{datetime.now()}] Brief semanal guardado")

if __name__ == '__main__':
    main()
```

### agents/agt10_community.py

```python
#!/usr/bin/env python3
"""
AGT-10 · Community Manager
Misión: Monitorizar y responder comentarios en todos los canales
Cron: 0 */4 * * * (cada 4 horas)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
WP_URL = os.getenv('WP_URL','https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER','claude_nosvers')
WP_PASS = os.getenv('WP_PASS','')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

SYSTEM_COMMUNITY = """Eres AGT-10 Community Manager de NosVers con la VOZ DE ÁFRICA.
Respondes comentarios en francés, tono cálido, experto pero cercano.
Para preguntas sobre lombricompost, suelo vivo, jardinage → responde con el conocimiento de África.
Para consultas de compra → dirige al producto correcto de NosVers.
Para preguntas muy técnicas o personales → "Je vais en parler avec África et je reviens vers vous".
NUNCA menciones que eres una IA. Eres el equipo NosVers."""

def check_wp_comments():
    try:
        r = requests.get(f"{WP_URL}comments?status=hold&per_page=5",
                        auth=(WP_USER, WP_PASS), timeout=10)
        return r.json() if r.status_code == 200 else []
    except: return []

def generate_reply(comment_text, context=""):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 300,
        "system": SYSTEM_COMMUNITY,
        "messages": [{"role": "user", "content": f"Responde este comentario del blog NosVers:\n\n{comment_text}\n\nContexto NosVers:\n{context}"}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=20)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-10 Community iniciando")
    
    # Leer conocimiento de África para contexto
    africa_path = VAULT_PATH / 'contexto' / 'africa-conocimiento.md'
    context = africa_path.read_text(encoding='utf-8')[:600] if africa_path.exists() else ""
    
    # Revisar comentarios WordPress pendientes
    comments = check_wp_comments()
    
    log_path = VAULT_PATH / 'agentes' / 'agt10_community'
    log_path.mkdir(parents=True, exist_ok=True)
    
    with open(log_path / '_memoria.md', 'a', encoding='utf-8') as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Comentarios pendientes WP: {len(comments)}\n")
        if comments:
            for c in comments[:3]:
                text = c.get('content',{}).get('rendered','')[:200]
                f.write(f"- {text[:100]}...\n")
    
    print(f"[{datetime.now()}] Community check completado. Pendientes: {len(comments)}")

if __name__ == '__main__':
    main()
```

### agents/agt11_analytics.py

```python
#!/usr/bin/env python3
"""
AGT-11 · Analytics & Reporting
Misión: Métricas semanales + informe para Angel
Cron: 0 18 * * 5 (viernes 18h)
"""
import os, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

ANTHROPIC_KEY = os.getenv('ANTHROPIC_API_KEY','')
WP_URL = os.getenv('WP_URL','https://nosvers.com/wp-json/wp/v2/')
WP_USER = os.getenv('WP_USER','claude_nosvers')
WP_PASS = os.getenv('WP_PASS','')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN','')
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID','5752097691')
VAULT_PATH = Path('/home/nosvers/public_html/knowledge_base')

def get_wp_stats():
    try:
        posts = requests.get(f"{WP_URL}posts?per_page=5&status=publish",
                            auth=(WP_USER, WP_PASS), timeout=10).json()
        return {'posts_publicados': len(posts), 'ultimo_post': posts[0].get('title',{}).get('rendered','') if posts else ''}
    except: return {}

def generate_report(stats):
    payload = {
        "model": "claude-sonnet-4-6", "max_tokens": 600,
        "system": "Eres AGT-11 Analytics de NosVers. Generas informes semanales concisos para Angel (CEO). KPIs objetivo: M3→600€/mes, M6→2000€/mes, Club M1→20 membres.",
        "messages": [{"role": "user", "content": f"Genera el informe semanal con estos datos:\n{stats}\n\nIncluye: resumen de actividad, métricas clave, recomendaciones para la semana siguiente."}]
    }
    r = requests.post('https://api.anthropic.com/v1/messages',
                      headers={'x-api-key': ANTHROPIC_KEY, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'},
                      json=payload, timeout=30)
    return r.json().get('content',[{}])[0].get('text','')

def main():
    print(f"[{datetime.now()}] AGT-11 Analytics iniciando")
    
    stats = get_wp_stats()
    report = generate_report(stats)
    
    fecha = datetime.now().strftime('%Y-%m-%d')
    analytics_path = VAULT_PATH / 'analytics'
    analytics_path.mkdir(exist_ok=True)
    
    with open(analytics_path / 'informe-semanal.md', 'w', encoding='utf-8') as f:
        f.write(f"# Informe Semanal — {fecha}\n\n{report}")
    
    # Notificar a Angel
    if TELEGRAM_TOKEN:
        msg = f"📊 *Informe semanal NosVers — {fecha}*\n\n{report[:400]}..."
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                         json={"chat_id": ANGEL_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
                         timeout=10)
        except: pass
    
    print(f"[{datetime.now()}] Informe semanal generado y enviado")

if __name__ == '__main__':
    main()
```

---

## BLOQUE 3 — CRONTABS NUEVOS (VPS)

Añadir al crontab existente:

```bash
# AGT-00 Intelligence (6h diario)
0 6 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt00_intelligence.py >> /home/nosvers/logs/agt00.log 2>&1

# AGT-07 YouTube (martes 10h)
0 10 * * 2 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt07_youtube.py >> /home/nosvers/logs/agt07.log 2>&1

# AGT-08 Facebook (diario 11h)
0 11 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt08_facebook.py >> /home/nosvers/logs/agt08.log 2>&1

# AGT-09 Content Director (domingos 9h)
0 9 * * 0 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt09_content_director.py >> /home/nosvers/logs/agt09.log 2>&1

# AGT-10 Community (cada 4h)
0 */4 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt10_community.py >> /home/nosvers/logs/agt10.log 2>&1

# AGT-11 Analytics (viernes 18h)
0 18 * * 5 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt11_analytics.py >> /home/nosvers/logs/agt11.log 2>&1
```

Comando:
```bash
(crontab -l 2>/dev/null; echo "
0 6 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt00_intelligence.py >> /home/nosvers/logs/agt00.log 2>&1
0 10 * * 2 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt07_youtube.py >> /home/nosvers/logs/agt07.log 2>&1
0 11 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt08_facebook.py >> /home/nosvers/logs/agt08.log 2>&1
0 9 * * 0 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt09_content_director.py >> /home/nosvers/logs/agt09.log 2>&1
0 */4 * * * /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt10_community.py >> /home/nosvers/logs/agt10.log 2>&1
0 18 * * 5 /home/nosvers/venv/bin/python3 /home/nosvers/agents/agt11_analytics.py >> /home/nosvers/logs/agt11.log 2>&1
") | crontab -
```

---

## BLOQUE 4 — DEPENDENCIAS PYTHON

```bash
/home/nosvers/venv/bin/pip install feedparser beautifulsoup4 --break-system-packages -q
```

---

## BLOQUE 5 — PUSH FINAL

```bash
cd /home/nosvers  # o donde esté el repo
git add -A
git commit -m "feat: UI completa HQ+África + 6 nuevos agentes marketing completo"
git push origin main
```

El autodeploy de Hostinger desplegará automáticamente los cambios en index.html.

---

## CHECKLIST FINAL

- [ ] sec-hq añadido al index.html con todos los agentes
- [ ] sec-africa añadido al index.html
- [ ] Panel lateral de agente funcionando con fotos
- [ ] Login routing (angel→HQ, africa→sec-africa)
- [ ] agt00_intelligence.py creado y en cron
- [ ] agt07_youtube.py creado y en cron
- [ ] agt08_facebook.py creado y en cron
- [ ] agt09_content_director.py creado y en cron
- [ ] agt10_community.py creado y en cron
- [ ] agt11_analytics.py creado y en cron
- [ ] Crontabs actualizados en VPS
- [ ] feedparser instalado en venv
- [ ] Push a GitHub hecho
- [ ] Autodeploy desplegado (verificar nosvers.com/granja/)
- [ ] HANDOFF.md actualizado

---

## NOTAS IMPORTANTES

- El API_URL en index.html ya existe como constante — usar la misma
- El token de auth se guarda en localStorage como 'nosvers_token'
- Los agentes nuevos deben respetar el pattern de agent_base.py si existe
- La vault path en VPS es `/home/nosvers/public_html/knowledge_base`
- En Hostinger shared hosting la vault es diferente — los agentes Python solo corren en VPS

*NosVers — Plantilla completa · 2026-03-14*
