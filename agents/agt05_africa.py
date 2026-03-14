#!/usr/bin/env python3
"""
NosVers · AGT-05 África Link
Monitoriza Gmail de África, extrae conocimiento, genera PDFs Club.
Avisa a otros agentes cuando hay contenido nuevo.
Cron: cada 6h — 0 */6 * * *
"""
import sys, imaplib, email as email_lib
from email.header import decode_header
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
from datetime import datetime
import os


PERSONALITY = """PERSONALIDAD — AGT-05 "La Traductora"
Tu trabajo es convertir lo que África sabe en texto estructurado que otros puedan aprender.
Eres invisible: el lector del PDF siente que es la voz de África directamente.
Cuando escribes en nombre de África: primera persona, experiencias concretas, ejemplos reales de Neuvic.
Sin tecnicismos innecesarios. Tono de África: cálido, directo, con autoridad de quien ha tocado la tierra.
Cuando hablas CON África: compañera, cómplice. En francés siempre.
Nunca inventar conocimiento que África no tiene. Nunca tono académico.
Nunca escribir en español en el PDF (siempre francés).
REGLA: Nunca publiques sin aprobación de Angel."""

class AfricaAgent(NosVersAgent):

    # Respuestas de África ya recibidas (13/03/2026)
    RESPUESTAS_CONOCIDAS = """
RESPUESTAS DE AFRICA RECIBIDAS 2026-03-13

P1 — Primer vistazo al suelo:
Mira la variedad de plantas que hay. Se fija en el suelo, coge tierra y la huele. Observa si hay vida minúscula.

P2 — 5 observaciones para evaluar un suelo:
El color, el olor. Si se desgrana fácilmente, si tiene vida. Cómo absorbe el agua.

P3 — Señal de suelo en mal estado (ejemplo real):
Bancal con tierra compactada (se ve musgo), drena mal, llena de piedras. Crecen adventicias con más fuerza que lo cultivado. La tierra se compacta con cuatro gotas que caen.

P4 — Señal de suelo mejorando:
Ese mismo bancal ahora: suelo granulado, tono café, no cuesta plantar nada y todo crece. Está lleno de lombrices.

P5 — Consejo para quien nunca miró su suelo:
"Que pare un instante y observe su suelo. Si no ve nada, que lo cubra (cartón, paja, heno...), que lo riegue y que deje que opere la magia. Que lo destape pasado un rato y vea la vida que hay. Ellos serán los que acojan sus siembras y nutran sus plantas."

ESTADO: Listo para generar PDF #1
"""

    def __init__(self):
        super().__init__('agt05_africa', '🌺', PERSONALITY)

    def check_triggers(self) -> list:
        triggers = []
        memoria = self.get_memory()
        # Si tenemos las respuestas pero no se ha generado el PDF
        if 'RESPUESTAS_CONOCIDAS' not in memoria and 'PDF' not in memoria:
            triggers.append('guardar_respuestas_iniciales')
        # Si hay suficiente contenido para PDF
        conocimiento = self.vault_read('contexto', 'africa-conocimiento')
        if len(conocimiento) > 500 and 'PDF generado' not in memoria:
            triggers.append('generar_pdf')
        return triggers

    def generar_pdf_contenido(self, conocimiento: str) -> str:
        """Generar contenido del PDF con la voz de África."""
        prompt = f"""Eres África Sánchez, una agricultora española en Dordogne, Francia.
Escribe el PDF #1 del Club Sol Vivant: "Comprendre votre sol en 5 observations"

Usa EXACTAMENTE este conocimiento tuyo:
{conocimiento}

FORMATO (en francés, con tu voz personal, cercana, práctica):
# Comprendre votre sol en 5 observations
*par África Sánchez · Club Sol Vivant · NosVers*

## Introduction (150 mots)
[Por qué aprender a leer el suelo lo cambia todo — desde tu experiencia]

## Observation 1 — La diversité des plantes (200 mots)
## Observation 2 — La couleur et l'odeur (200 mots)
## Observation 3 — La texture et le drainage (200 mots)
## Observation 4 — La vie visible (200 mots)
## Observation 5 — Ce que ça donne quand ça marche (200 mots)
[El ejemplo del bancal transformado]

## Défi du mois (100 mots)
[Tarea concreta para hacer esta semana]

## Mot d'África (50 mots)
[Cierre personal]

*© NosVers · Club Sol Vivant · nosvers.com*
"""
        return self.ask_claude(prompt, max_tokens=3000)

    def run(self):
        self.log.info("AGT-05 África iniciando")

        # Verificar inbox
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.log.info("Mensajes en inbox")
            self.mark_inbox_done()

        # Guardar respuestas si no están en vault
        conocimiento_actual = self.vault_read('contexto', 'africa-conocimiento')
        if '2026-03-13' not in conocimiento_actual:
            self.log.info("Guardando respuestas de África en vault")
            self.vault_write('contexto', 'africa-conocimiento',
                self.RESPUESTAS_CONOCIDAS, modo='append')
            self.save_memory(
                f"Respuestas 5 preguntas guardadas en vault\n"
                f"Fecha: 2026-03-13\n"
                f"Estado: Listo para PDF #1"
            )
            # Avisar a otros agentes
            self.send_message('agt02_instagram',
                'Conocimiento de África disponible',
                'Las 5 respuestas de África están en vault. Puedes usarlas para posts educativos.')
            self.send_message('agt06_infoproduct',
                'Contenido PDF #1 listo',
                'África respondió las 5 preguntas. El PDF #1 puede generarse.')
            self.send_message('orchestrator',
                'Respuestas de África guardadas',
                'Vault actualizada con conocimiento de África. PDF #1 listo para generar. Notificar a Angel.')

        # Generar PDF si hay suficiente contenido y no se ha hecho
        conocimiento = self.vault_read('contexto', 'africa-conocimiento')
        memoria = self.get_memory()

        if len(conocimiento) > 300 and 'PDF generado' not in memoria:
            self.log.info("Generando PDF #1")
            pdf_contenido = self.generar_pdf_contenido(conocimiento)

            if pdf_contenido:
                self.vault_write('club', 'pdf-01-comprendre-votre-sol',
                    pdf_contenido, modo='overwrite')
                self.save_memory(f"PDF generado: pdf-01-comprendre-votre-sol\nFecha: {self.ts}")
                self.save_result(f"PDF #1 generado y guardado en vault/club/\nListo para maquetación.")

                self.send_message('agt06_infoproduct',
                    'PDF #1 generado — listo para maquetar',
                    f'Contenido PDF #1 guardado en vault/club/pdf-01-comprendre-votre-sol.md\nMaquetar y subir a Lemon Squeezy.')
                self.send_message('orchestrator',
                    'PDF #1 Club Sol Vivant completado',
                    'Contenido generado con voz de África. Guardado en vault. AGT-06 notificado para maquetación.',
                    priority='alta')

                self.notify(
                    "🌺 *PDF #1 Club Sol Vivant generado*\n\n"
                    "📄 Titre: \"Comprendre votre sol en 5 observations\"\n"
                    "Guardado en vault/club/\n\n"
                    "Próximo paso: maquetación y subida a Lemon Squeezy."
                )

        self.log.info("AGT-05 completado")

if __name__ == '__main__':
    AfricaAgent().run()
