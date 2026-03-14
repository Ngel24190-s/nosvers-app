#!/usr/bin/env python3
"""
NosVers · Agent Base
Clase base compartida por todos los agentes.
Incluye: vault read/write, mensajería inter-agente, logging, notificaciones.
"""
import os, json, logging, requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

VAULT       = Path(os.getenv('VAULT_PATH', '/home/nosvers/public_html/knowledge_base'))
APP_URL     = os.getenv('APP_URL', 'https://nosvers.com/granja/api.php')
APP_TOKEN   = os.getenv('APP_TOKEN', '')
TG_TOKEN    = os.getenv('TELEGRAM_TOKEN', '')
ANGEL_ID    = os.getenv('ANGEL_CHAT_ID', '5752097691')
CLAUDE_KEY  = os.getenv('ANTHROPIC_API_KEY', '')
WP_URL      = os.getenv('WP_URL', '')
WP_USER     = os.getenv('WP_USER', '')
WP_PASS     = os.getenv('WP_PASS', '')


class NosVersAgent:
    """Clase base para todos los agentes de NosVers."""

    def __init__(self, name: str, icon: str = "🤖", personality: str = ""):
        self.name  = name
        self.icon  = icon
        self.personality = personality
        self.vault = VAULT
        self.log   = self._setup_log()
        self.ts    = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── LOGGING ───────────────────────────────────────────
    def _setup_log(self):
        log_dir = Path('/home/nosvers/logs')
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s [{self.name}] %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f'{self.name}.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(self.name)

    # ── VAULT ──────────────────────────────────────────────
    def vault_read(self, categoria: str, archivo: str) -> str:
        fp = self.vault / categoria / f"{archivo}.md"
        if fp.exists():
            return fp.read_text(encoding='utf-8')
        # Fallback via API
        try:
            r = requests.get(f"{APP_URL}?action=vault_read&category={categoria}&filename={archivo}",
                           headers={'X-App-Token': APP_TOKEN}, timeout=10)
            return r.json().get('content', '')
        except:
            return ''

    def vault_write(self, categoria: str, archivo: str, contenido: str, modo: str = 'append'):
        fp = self.vault / categoria / f"{archivo}.md"
        fp.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        if modo == 'overwrite' or not fp.exists():
            fp.write_text(f"# {archivo}\n*Creado: {ts}*\n\n{contenido}", encoding='utf-8')
        else:
            with open(fp, 'a', encoding='utf-8') as f:
                f.write(f"\n\n---\n*{ts}*\n\n{contenido}")
        self.log.info(f"vault_write: {categoria}/{archivo}.md ({modo})")

    def vault_list(self, categoria: str = '') -> list:
        base = self.vault / categoria if categoria else self.vault
        if not base.exists():
            return []
        return [str(f.relative_to(self.vault)) for f in base.rglob('*.md')]

    # ── MENSAJERÍA INTER-AGENTE ────────────────────────────
    def send_message(self, to_agent: str, subject: str, body: str, priority: str = 'normal'):
        """Enviar mensaje a otro agente via vault."""
        msg = f"## [{self.ts}] DE: {self.name} → PARA: {to_agent}\n"
        msg += f"**Asunto:** {subject}\n"
        msg += f"**Prioridad:** {priority}\n\n"
        msg += f"{body}\n\n"
        msg += f"*Estado: PENDIENTE*"
        self.vault_write(f'agentes/{to_agent}', '_inbox', msg, modo='append')
        self.log.info(f"Mensaje enviado a {to_agent}: {subject}")

    def read_inbox(self) -> str:
        """Leer mensajes pendientes de otros agentes."""
        content = self.vault_read(f'agentes/{self.name}', '_inbox')
        return content

    def mark_inbox_done(self):
        """Marcar inbox como procesado."""
        inbox = self.read_inbox()
        if inbox:
            done = inbox.replace('*Estado: PENDIENTE*', f'*Estado: PROCESADO {self.ts}*')
            self.vault_write(f'agentes/{self.name}', '_inbox', done, modo='overwrite')

    def broadcast(self, subject: str, body: str, agents: list = None):
        """Enviar mensaje a múltiples agentes."""
        if agents is None:
            agents = ['orchestrator','agt01_visual','agt02_instagram','agt04_seo','agt05_africa']
        agents = [a for a in agents if a != self.name]
        for agent in agents:
            self.send_message(agent, subject, body)

    # ── MEMORIA PERSISTENTE ────────────────────────────────
    def save_memory(self, entry: str):
        """Guardar entrada en memoria del agente."""
        self.vault_write(f'agentes/{self.name}', '_memoria', entry, modo='append')

    def get_memory(self) -> str:
        """Leer memoria completa del agente."""
        return self.vault_read(f'agentes/{self.name}', '_memoria')

    def get_context(self) -> str:
        """Leer contexto predeterminado del agente."""
        return self.vault_read(f'agentes/{self.name}', '_contexto')

    def save_result(self, resultado: str):
        """Guardar último resultado (overwrite)."""
        self.vault_write(f'agentes/{self.name}', '_resultado', resultado, modo='overwrite')

    # ── CLAUDE API ─────────────────────────────────────────
    def ask_claude(self, prompt: str, contexto_extra: str = '', max_tokens: int = 1500) -> str:
        """Llamar a Claude con contexto del agente + vault."""
        if not CLAUDE_KEY:
            self.log.error("ANTHROPIC_API_KEY no configurada")
            return ''
        context = self.get_context()
        personality_block = f"\n{self.personality}\n" if self.personality else ""
        system = f"""Eres el agente {self.name} de NosVers, ferme lombricole en Dordogne, Francia.
{personality_block}
{context}
{contexto_extra}"""
        try:
            r = requests.post('https://api.anthropic.com/v1/messages',
                headers={'x-api-key': CLAUDE_KEY, 'anthropic-version': '2023-06-01',
                         'Content-Type': 'application/json'},
                json={'model': 'claude-sonnet-4-6', 'max_tokens': max_tokens,
                      'system': system, 'messages': [{'role': 'user', 'content': prompt}]},
                timeout=60)
            return r.json()['content'][0]['text']
        except Exception as e:
            self.log.error(f"Claude API error: {e}")
            return ''

    # ── TELEGRAM ───────────────────────────────────────────
    def notify(self, msg: str, chat_id: str = ANGEL_ID):
        """Notificar a Angel via Telegram."""
        if not TG_TOKEN:
            return
        try:
            requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": f"{self.icon} *{self.name}*\n\n{msg}",
                      "parse_mode": "Markdown"}, timeout=10)
        except Exception as e:
            self.log.error(f"Telegram error: {e}")

    # ── PROACTIVIDAD ───────────────────────────────────────
    def check_triggers(self) -> list:
        """
        Verificar si hay condiciones que requieren acción.
        Sobrescribir en cada agente para definir sus triggers.
        Returns: lista de acciones necesarias
        """
        return []

    def run(self):
        """
        Método principal. Sobrescribir en cada agente.
        Flujo estándar: leer inbox → check triggers → ejecutar → guardar memoria → notificar
        """
        self.log.info(f"Iniciando {self.name}")
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.log.info("Mensajes pendientes en inbox")
            self.process_inbox(inbox)
        triggers = self.check_triggers()
        if triggers:
            self.log.info(f"Triggers activos: {triggers}")
        self.mark_inbox_done()

    def process_inbox(self, inbox: str):
        """Procesar mensajes del inbox. Sobrescribir si se necesita lógica específica."""
        self.log.info(f"Procesando inbox: {len(inbox)} chars")
