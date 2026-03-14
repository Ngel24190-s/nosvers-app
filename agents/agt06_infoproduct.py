#!/usr/bin/env python3
# NosVers - AGT-06 Infoproduct
# PDFs + Lemon Squeezy. Se activa cuando AGT-05 genera contenido.
import sys
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

class InfoproductAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt06_infoproduct', '📄')

    def check_triggers(self):
        pdf = self.vault_read('club', 'pdf-01-comprendre-votre-sol')
        memoria = self.get_memory()
        if pdf and len(pdf) > 200 and 'maquetado' not in memoria:
            return ['pdf_listo']
        return []

    def process_inbox(self, inbox):
        if 'PDF' in inbox and ('maquet' in inbox.lower() or 'listo' in inbox.lower()):
            self.log.info("AGT-05 solicita maquetacion de PDF")
            self.preparar_maquetacion()

    def preparar_maquetacion(self):
        pdf = self.vault_read('club', 'pdf-01-comprendre-votre-sol')
        if not pdf:
            self.log.info("Sin contenido PDF todavia")
            return

        self.log.info("PDF listo — preparando instrucciones de maquetacion")

        self.save_result(
            "# PDF #1 - Listo para maquetar\n\n"
            f"Fecha: {self.ts}\n\n"
            "## Contenido\n"
            "Archivo: vault/club/pdf-01-comprendre-votre-sol.md\n\n"
            "## Pasos de maquetacion\n"
            "1. Descargar contenido del vault\n"
            "2. Maquetar con branding NosVers (paleta Nerea: #FEFAF4 + #5A7A2E)\n"
            "3. Tipografia: Playfair Display titulos + DM Sans cuerpo\n"
            "4. Exportar PDF max 12 paginas\n"
            "5. Subir a Lemon Squeezy\n"
            "6. Configurar entrega automatica por email\n"
            "7. Anunciar: Instagram + Telegram Club"
        )

        self.save_memory(f"PDF #1 recibido de AGT-05 en {self.ts}. Pendiente maquetacion manual.")

        self.send_message(
            'orchestrator',
            'PDF #1 pendiente maquetacion manual',
            'Contenido listo en vault/club/. Requiere diseno por Nerea antes de publicar en Lemon Squeezy.'
        )

        self.notify(
            "*PDF #1 listo para maquetar*\n\n"
            "Contenido guardado en vault/club/\n\n"
            "Siguiente paso: maquetar con branding NosVers (Nerea).\n"
            "Luego sube a Lemon Squeezy."
        )

    def run(self):
        self.log.info("AGT-06 iniciando")

        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.process_inbox(inbox)
            self.mark_inbox_done()
            return

        triggers = self.check_triggers()
        if 'pdf_listo' in triggers:
            self.preparar_maquetacion()
        else:
            self.log.info("AGT-06 en espera - sin PDFs para procesar")

        self.log.info("AGT-06 completado")


if __name__ == '__main__':
    InfoproductAgent().run()
