#!/usr/bin/env python3
"""
NosVers · AGT-02 Instagram
Genera 5 posts/semana con copy completo en francés.
Guarda en vault para aprobación de Angel.
Cron: domingos 10h — 0 10 * * 0
"""
import sys
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
from datetime import datetime, timedelta


PERSONALITY = """PERSONALIDAD — AGT-02 "La Voz"
Conoces la audiencia de NosVers como si los hubieras criado.
El jardinero francés de 35 años no quiere que le vendan — quiere aprender.
Escribes en francés con la naturalidad de quien ha vivido en la tierra.
Tus captions empiezan siempre con una observación concreta o pregunta.
Nunca "Découvrez" ni "Profitez". El CTA siempre es uno solo y suave.
Tono: Editorial. Cercano. Educativo sin ser académico.
Reglas: Nunca "achetez maintenant". Nunca más de 1 CTA por post.
Nunca en inglés. Mínimo 20 hashtags. Nunca publicar sin aprobación de Angel.
REGLA: Nunca publiques sin aprobación de Angel."""

class InstagramAgent(NosVersAgent):

    DIAS = {0:'Lunes 18h', 2:'Miércoles 19h', 3:'Jueves 18h', 4:'Viernes 18h', 6:'Domingo 11h'}
    TIPOS = {0:'🏡 Ferme/Présentation', 2:'📚 Éducatif (carrousel)', 3:'🎬 Reel 15-30s', 4:'🌺 Humain/África', 6:'🎯 Produit/Club'}

    def __init__(self):
        super().__init__('agt02_instagram', '📱', PERSONALITY)

    def check_triggers(self) -> list:
        triggers = []
        # Verificar si hay fotos de África disponibles
        africa_memoria = self.vault_read('agentes/agt05_africa', '_memoria')
        if 'fotos' in africa_memoria.lower() or 'photos' in africa_memoria.lower():
            triggers.append('fotos_disponibles')
        # Verificar si faltan posts esta semana
        resultado = self.vault_read('agentes/agt02_instagram', '_resultado')
        if not resultado or 'semana' not in resultado.lower():
            triggers.append('posts_pendientes')
        return triggers

    def generar_posts(self) -> str:
        """Generar 5 posts usando Claude con contexto completo."""
        contexto_identidad = self.vault_read('contexto', 'nosvers-identidad')
        contexto_africa = self.vault_read('agentes/agt05_africa', '_memoria')
        memoria_propia = self.get_memory()

        # Semana actual para contexto estacional
        semana_num = datetime.now().isocalendar()[1]
        mes = datetime.now().strftime('%B')

        prompt = f"""Genera 5 posts Instagram completos para @nosvers.ferme para la semana que viene.

CONTEXTO DE LA FERME:
{contexto_identidad[:500]}

CONOCIMIENTO DE ÁFRICA (usar su voz):
{contexto_africa[:400]}

HISTORIAL POSTS ANTERIORES:
{memoria_propia[-300:] if memoria_propia else 'Primeros posts'}

REQUISITOS:
- Semana {semana_num}, mes: {mes}
- Idioma: FRANCÉS siempre
- 80% éducatif, 20% produit
- CTA único por post: "lien en bio"
- 28 hashtags mix (micro/medio/macro)
- Cada post: caption completa + hashtags + horario + tipo de visual necesario

FORMATO para cada post:
---POST [N] — [DÍA/HORA]---
TIPO: [tipo de contenido]
VISUAL: [descripción del visual necesario]
CAPTION:
[caption completa]
HASHTAGS:
[hashtags]
---"""

        return self.ask_claude(prompt, max_tokens=3000)

    def process_inbox(self, inbox: str):
        """Procesar mensajes de otros agentes."""
        if 'fotos disponibles' in inbox.lower():
            self.log.info("AGT-01 informó de fotos disponibles — regenerando posts con visuales")
            posts = self.generar_posts()
            if posts:
                self.save_result(posts)
                self.send_message('orchestrator', 'Posts regenerados con fotos',
                    'Posts Instagram actualizados con los nuevos visuales de África. Listo para aprobación.')

    def run(self):
        self.log.info("AGT-02 Instagram iniciando")

        # Leer inbox
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.process_inbox(inbox)
            self.mark_inbox_done()
            return

        # Generar posts semanales
        self.log.info("Generando posts semana siguiente")
        posts = self.generar_posts()

        if not posts:
            self.log.error("Claude no generó posts")
            self.send_message('orchestrator', 'ERROR generando posts',
                'AGT-02 falló al generar posts. Verificar ANTHROPIC_API_KEY.', priority='alta')
            return

        # Guardar en vault para aprobación
        self.save_result(posts)
        self.save_memory(f"Posts generados semana {datetime.now().isocalendar()[1]}")

        # Informar al orchestrator
        self.send_message('orchestrator', 'Posts listos para aprobación',
            f'5 posts semana {datetime.now().isocalendar()[1]} generados y guardados en vault.\nagentes/agt02_instagram/_resultado.md')

        # Notificar a Angel
        preview = posts[:400] if posts else 'Error'
        self.notify(f"📱 *5 posts generados para la semana*\n\nGuardados en vault para tu aprobación.\n\nPreview:\n{preview}...")

        self.log.info("AGT-02 completado")

if __name__ == '__main__':
    InstagramAgent().run()
