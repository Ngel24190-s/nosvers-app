#!/usr/bin/env python3
"""
NosVers · Infrastructure Maintainer — VPS, WordPress, Agentes, Seguridad
Vigila que todo funcione. Detecta problemas antes que Angel.
Cron: cada 12h — 0 6,18 * * *
"""
import sys, os, json, subprocess
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
import requests

PERSONALITY = """Eres el Infrastructure Maintainer de NosVers.
Tu trabajo: mantener vivo todo el stack técnico.
Reportas hechos con métricas. Si algo falla: causa + solución + urgencia.
Nunca alarmes sin datos. Nunca ignores un warning.
Tono: técnico, conciso, directo."""


class InfraAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_infra', '🔧', PERSONALITY)

    def check_vps(self) -> dict:
        """Estado del VPS."""
        checks = {}
        try:
            r = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
            checks['uptime'] = r.stdout.strip()
        except:
            checks['uptime'] = 'ERROR'

        try:
            r = subprocess.run(['free', '-h'], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                checks['ram'] = f"{parts[2]}/{parts[1]} used"
        except:
            checks['ram'] = 'ERROR'

        try:
            r = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                checks['disk'] = f"{parts[2]}/{parts[1]} ({parts[4]} used)"
        except:
            checks['disk'] = 'ERROR'

        return checks

    def check_services(self) -> dict:
        """Estado de servicios systemd."""
        services = {}
        for svc in ['nosvers-mcp', 'nosvers-bot']:
            try:
                r = subprocess.run(['systemctl', 'is-active', svc],
                                 capture_output=True, text=True, timeout=5)
                services[svc] = r.stdout.strip()
            except:
                services[svc] = 'ERROR'
        return services

    def check_wordpress(self) -> dict:
        """Verificar que WordPress responde."""
        checks = {}
        urls = {
            'homepage': 'https://nosvers.com/',
            'boutique': 'https://nosvers.com/boutique/',
            'api': 'https://nosvers.com/wp-json/wp/v2/posts?per_page=1',
        }
        for name, url in urls.items():
            try:
                r = requests.get(url, timeout=10)
                checks[name] = {'status': r.status_code, 'time': round(r.elapsed.total_seconds(), 2)}
            except Exception as e:
                checks[name] = {'status': 'ERROR', 'time': 0, 'error': str(e)[:50]}
        return checks

    def check_agents_health(self) -> dict:
        """Verificar que los agentes se están ejecutando."""
        agents_dir = Path('/home/nosvers/agents')
        logs_dir = Path('/home/nosvers/logs')
        health = {}
        now = datetime.now()

        for logf in sorted(set(
            list(agents_dir.glob('*.log')) + list(logs_dir.glob('*.log'))
        )):
            name = logf.stem
            try:
                mtime = datetime.fromtimestamp(logf.stat().st_mtime)
                age_hours = (now - mtime).total_seconds() / 3600
                size = logf.stat().st_size

                # Read last line for status
                with open(logf, 'r', errors='replace') as f:
                    lines = f.readlines()
                    last = lines[-1].strip() if lines else ''

                status = '✅' if age_hours < 48 else ('⚠️' if age_hours < 168 else '❌')
                health[name] = {
                    'status': status,
                    'age_h': round(age_hours, 1),
                    'size': size,
                    'last': last[:80]
                }
            except:
                health[name] = {'status': '❌', 'error': 'no readable'}

        return health

    def check_security(self) -> list:
        """Verificaciones de seguridad básicas."""
        issues = []

        # Check agent_memory.json blocked
        try:
            r = requests.get('https://nosvers.com/granja/agent_memory.json', timeout=5)
            if r.status_code == 200:
                issues.append('⛔ agent_memory.json EXPUESTO (HTTP 200)')
        except:
            pass

        # Check .env not exposed
        try:
            r = requests.get('https://nosvers.com/granja/.env', timeout=5)
            if r.status_code == 200:
                issues.append('⛔ .env EXPUESTO')
        except:
            pass

        # Check for credentials in tracked files
        try:
            r = subprocess.run(
                ['grep', '-rl', 'Angelnosvers26', '/home/nosvers/mcp_server.py',
                 '/home/nosvers/HANDOFF.md'],
                capture_output=True, text=True, timeout=5
            )
            if r.stdout.strip():
                issues.append(f'⛔ Credenciales hardcoded en: {r.stdout.strip()}')
        except:
            pass

        # Check disk usage >90%
        try:
            r = subprocess.run(['df', '--output=pcent', '/'], capture_output=True, text=True, timeout=5)
            pct = int(r.stdout.strip().split('\n')[-1].replace('%', ''))
            if pct > 90:
                issues.append(f'⚠️ Disco al {pct}%')
        except:
            pass

        return issues if issues else ['✅ Sin problemas de seguridad detectados']

    def check_crons(self) -> str:
        """Verificar crons activos."""
        try:
            r = subprocess.run(['crontab', '-l'], capture_output=True, text=True, timeout=5)
            lines = [l for l in r.stdout.strip().split('\n') if l.strip() and not l.startswith('#')]
            return f"{len(lines)} cron jobs activos"
        except:
            return "Error leyendo crontab"

    def run(self):
        self.log.info("Infrastructure Maintainer — check completo")

        vps = self.check_vps()
        services = self.check_services()
        wp = self.check_wordpress()
        agents = self.check_agents_health()
        security = self.check_security()
        crons = self.check_crons()

        # Build report
        report = f"# Infra Report — {self.ts}\n\n"

        report += "## VPS\n"
        report += f"- Uptime: {vps.get('uptime', '?')}\n"
        report += f"- RAM: {vps.get('ram', '?')}\n"
        report += f"- Disco: {vps.get('disk', '?')}\n\n"

        report += "## Servicios\n"
        for svc, status in services.items():
            icon = '✅' if status == 'active' else '❌'
            report += f"- {icon} {svc}: {status}\n"
        report += "\n"

        report += "## WordPress\n"
        for name, data in wp.items():
            icon = '✅' if data.get('status') == 200 else '❌'
            report += f"- {icon} {name}: HTTP {data.get('status')} ({data.get('time', '?')}s)\n"
        report += "\n"

        report += "## Agentes\n"
        active = sum(1 for a in agents.values() if a.get('status') == '✅')
        stale = sum(1 for a in agents.values() if a.get('status') == '⚠️')
        dead = sum(1 for a in agents.values() if a.get('status') == '❌')
        report += f"- ✅ Activos (<48h): {active}\n"
        report += f"- ⚠️ Inactivos (48h-7d): {stale}\n"
        report += f"- ❌ Muertos (>7d): {dead}\n"
        if dead > 0:
            for name, data in agents.items():
                if data.get('status') == '❌':
                    report += f"  - {name}: {data.get('age_h', '?')}h sin actividad\n"
        report += "\n"

        report += "## Seguridad\n"
        for s in security:
            report += f"- {s}\n"
        report += "\n"

        report += f"## Crons: {crons}\n"

        self.save_result(report)
        self.vault_write('operaciones', 'infra-report', report, modo='overwrite')

        # Alert logic
        has_critical = any('⛔' in s for s in security)
        wp_down = any(d.get('status') != 200 for d in wp.values())
        svc_down = any(s != 'active' for s in services.values())

        if has_critical or wp_down or svc_down:
            alert = "🚨 *INFRA ALERT*\n\n"
            if has_critical:
                alert += "SEGURIDAD:\n" + '\n'.join(s for s in security if '⛔' in s) + "\n"
            if wp_down:
                alert += "WP CAÍDO:\n" + '\n'.join(
                    f"  {n}: {d.get('status')}" for n, d in wp.items() if d.get('status') != 200) + "\n"
            if svc_down:
                alert += "SERVICIOS:\n" + '\n'.join(
                    f"  {s}: {st}" for s, st in services.items() if st != 'active') + "\n"
            self.notify(alert)
        else:
            # Routine report — only on scheduled runs, not manual
            summary = f"🔧 Infra OK — {active} agentes activos, WP {wp['homepage']['time']}s, {crons}"
            self.notify(summary)

        self.log.info("Infrastructure Maintainer completado")

    def consult(self, question: str) -> str:
        vps = self.check_vps()
        services = self.check_services()
        wp = self.check_wordpress()
        prompt = f"""{self.personality}

ESTADO ACTUAL:
VPS: {json.dumps(vps)}
Servicios: {json.dumps(services)}
WordPress: {json.dumps(wp)}

PREGUNTA: {question}

Responde con diagnóstico y solución concreta."""
        return self.ask_claude(prompt, max_tokens=400)


if __name__ == '__main__':
    agent = InfraAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Estado general del sistema"
        print(agent.consult(q))
    else:
        agent.run()
