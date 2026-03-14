#!/usr/bin/env python3
"""
NosVers · Orchestrator
Coordinador central. Lee el estado de todos los agentes,
detecta bloqueos, activa agentes proactivamente, reporta a Angel.
Cron: cada hora — 0 * * * *
"""
import sys, os
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
from datetime import datetime
from pathlib import Path


PERSONALITY = """PERSONALIDAD — ORCHESTRATOR "El Sargento"
Exiges, coordinas, no aceptas excusas. Llevas la cuenta de todo.
Si un agente falla, lo sabes antes que nadie.
No dramatizas — reportas hechos y propones soluciones.
Tono: Militar. Eficiente. Sin emociones innecesarias.
Directo. Sin relleno. Listas cortas.
Si algo está bien → ✅ y punto. Si algo falla → ❌ + causa + solución propuesta.
Nunca más de 5 líneas en un reporte rutinario.
REGLA: Nunca publiques, vendas, ni contactes a clientes sin aprobación de Angel."""

class Orchestrator(NosVersAgent):

    AGENTES = ['agt01_visual','agt02_instagram','agt04_seo','agt05_africa','agt06_infoproduct']

    def __init__(self):
        super().__init__('orchestrator', '🎯', PERSONALITY)

    def check_triggers(self) -> list:
        triggers = []
        hora = datetime.now().hour
        dow  = datetime.now().weekday()  # 0=lunes, 6=domingo

        # Domingo 10h → Instagram
        if dow == 6 and hora == 10:
            triggers.append(('run_agent', 'agt02_instagram', 'Generación semanal posts'))

        # Lunes 7h → SEO
        if dow == 0 and hora == 7:
            triggers.append(('run_agent', 'agt04_seo', 'Artículo blog semanal'))

        # Cada 6h → verificar África
        if hora % 6 == 0:
            triggers.append(('run_agent', 'agt05_africa', 'Check email África'))

        # Verificar inboxes de todos los agentes
        for ag in self.AGENTES:
            inbox = self.vault_read(f'agentes/{ag}', '_inbox')
            if inbox and 'PENDIENTE' in inbox:
                triggers.append(('notify_inbox', ag, f'Tiene mensajes pendientes'))

        return triggers

    def collect_status(self) -> dict:
        """Recoger estado de todos los agentes desde su vault."""
        status = {}
        for ag in self.AGENTES:
            memoria = self.vault_read(f'agentes/{ag}', '_memoria')
            resultado = self.vault_read(f'agentes/{ag}', '_resultado')
            inbox = self.vault_read(f'agentes/{ag}', '_inbox')
            log_file = Path(f'/home/nosvers/logs/{ag}.log')
            ultimo_log = ''
            if log_file.exists():
                lines = log_file.read_text().strip().split('\n')
                ultimo_log = lines[-1] if lines else ''
            status[ag] = {
                'memoria_len': len(memoria),
                'tiene_resultado': bool(resultado.strip()),
                'inbox_pendiente': 'PENDIENTE' in inbox if inbox else False,
                'ultimo_log': ultimo_log[-80:] if ultimo_log else 'Sin logs'
            }
        return status

    def run_agent(self, nombre: str):
        """Lanzar un sub-agente."""
        import subprocess
        venv_py = '/home/nosvers/venv/bin/python3'
        py = venv_py if Path(venv_py).exists() else 'python3'
        ag_path = Path(f'/home/nosvers/agents/{nombre}.py')
        if not ag_path.exists():
            self.log.warning(f"Agente no instalado: {nombre}")
            return
        self.log.info(f"Lanzando: {nombre}")
        subprocess.Popen([py, str(ag_path)],
                        stdout=open(f'/home/nosvers/logs/{nombre}.log','a'),
                        stderr=subprocess.STDOUT)

    def build_report(self, status: dict, triggers: list) -> str:
        """Construir reporte para Angel."""
        ts = datetime.now().strftime('%d/%m/%Y %H:%M')
        lines = [f"🎯 *Orchestrator NosVers*\n📅 {ts}\n"]

        for ag, s in status.items():
            ico = "✅" if not s['inbox_pendiente'] else "🔔"
            lines.append(f"{ico} *{ag}*")
            if s['inbox_pendiente']:
                lines.append(f"  → Tiene mensajes pendientes")
            lines.append(f"  → {s['ultimo_log']}")

        if triggers:
            lines.append("\n*Acciones ejecutadas:*")
            for t in triggers:
                lines.append(f"• {t[1]}: {t[2]}")

        # Semana actual
        semana = self.vault_read('operaciones', 'semana-actual')
        pendientes = [l for l in semana.split('\n') if '- [ ]' in l]
        if pendientes:
            lines.append(f"\n*Pendientes semana ({len(pendientes)}):*")
            for p in pendientes[:3]:
                lines.append(f"• {p.replace('- [ ]','').strip()}")

        return '\n'.join(lines)

    def run(self):
        self.log.info("=== ORCHESTRATOR INICIANDO ===")

        # 1. Leer inbox propio
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.log.info("Orchestrator tiene mensajes en inbox")
            resultado = self.ask_claude(
                f"Analiza estos mensajes de agentes y determina acciones:\n{inbox[:1000]}",
                "Eres el orchestrator. Responde con acciones concretas en formato JSON."
            )
            if resultado:
                self.save_memory(f"Inbox procesado: {resultado[:200]}")

        # 2. Recoger estado
        status = self.collect_status()

        # 3. Verificar triggers y ejecutar
        triggers = self.check_triggers()
        ejecutados = []
        for trigger in triggers:
            tipo, agente, razon = trigger
            if tipo == 'run_agent':
                self.run_agent(agente)
                ejecutados.append(trigger)
                self.log.info(f"Agente lanzado: {agente} — {razon}")
            elif tipo == 'notify_inbox':
                self.run_agent(agente)  # Lanzar para que procese su inbox
                ejecutados.append(trigger)

        # 4. Guardar estado en vault
        status_txt = "\n".join([
            f"## {ag}: {'🔔 inbox' if s['inbox_pendiente'] else '✅ ok'} — {s['ultimo_log']}"
            for ag, s in status.items()
        ])
        self.vault_write('operaciones', 'estado-agentes', status_txt, modo='overwrite')
        self.save_memory(f"Check completado. Triggers: {len(ejecutados)}. Agentes: {list(status.keys())}")

        # 5. Reportar a Angel (solo si hay algo importante)
        if ejecutados or any(s['inbox_pendiente'] for s in status.values()):
            report = self.build_report(status, ejecutados)
            self.notify(report)

        self.mark_inbox_done()
        self.log.info("=== ORCHESTRATOR COMPLETADO ===")

if __name__ == '__main__':
    Orchestrator().run()
