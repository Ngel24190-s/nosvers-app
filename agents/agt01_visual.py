#!/usr/bin/env python3
# NosVers - AGT-01 Visual Director
# Procesa fotos de Africa, avisa a AGT-02 cuando hay material listo
import sys
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent, CLAUDE_KEY
from pathlib import Path
import base64, json, re
import requests as req

class VisualAgent(NosVersAgent):

    UPLOADS = Path('/home/nosvers/uploads/africa')
    VISUELS = Path('/home/nosvers/uploads/visuels')

    def __init__(self):
        super().__init__('agt01_visual', '📷')
        self.UPLOADS.mkdir(parents=True, exist_ok=True)
        self.VISUELS.mkdir(parents=True, exist_ok=True)

    def check_triggers(self):
        memoria = self.get_memory()
        exts = ['*.jpg','*.jpeg','*.png','*.JPG','*.JPEG','*.PNG']
        fotos = []
        for ext in exts:
            fotos += list(self.UPLOADS.glob(ext))
        nuevas = [f for f in fotos if f.name not in memoria]
        return [('fotos_nuevas', nuevas)] if nuevas else []

    def analizar_foto(self, foto_path):
        try:
            with open(foto_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            pregunta = ("Analiza esta foto para @nosvers.ferme en Instagram. "
                       "Responde SOLO en JSON valido sin markdown: "
                       "{\"apta\": true, \"categoria\": \"vers\", \"caption_sugerida\": \"...\", \"razon\": \"...\"}")
            r = req.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': CLAUDE_KEY,
                    'anthropic-version': '2023-06-01',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'claude-sonnet-4-6',
                    'max_tokens': 400,
                    'messages': [{'role': 'user', 'content': [
                        {'type': 'image', 'source': {
                            'type': 'base64',
                            'media_type': 'image/jpeg',
                            'data': img_b64
                        }},
                        {'type': 'text', 'text': pregunta}
                    ]}]
                },
                timeout=30
            )
            text = r.json()['content'][0]['text']
            clean = re.sub(r'```json|```', '', text).strip()
            return json.loads(clean)
        except Exception as e:
            self.log.error(f"Error analizando foto {foto_path.name}: {e}")
            return {"apta": True, "categoria": "general", "caption_sugerida": "", "razon": "error"}

    def run(self):
        self.log.info("AGT-01 Visual iniciando")

        # Leer inbox
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.log.info("Procesando inbox")
            self.mark_inbox_done()

        # Check fotos nuevas
        triggers = self.check_triggers()
        fotos_ok = []

        for tipo, fotos in triggers:
            self.log.info(f"Procesando {len(fotos)} fotos nuevas")
            for foto in fotos:
                analisis = self.analizar_foto(foto)
                if analisis.get('apta'):
                    fotos_ok.append({
                        'archivo': foto.name,
                        'categoria': analisis.get('categoria', 'general'),
                        'caption': analisis.get('caption_sugerida', '')
                    })
                self.save_memory(
                    f"Foto procesada: {foto.name} | "
                    f"apta: {analisis.get('apta')} | "
                    f"cat: {analisis.get('categoria')}"
                )

        if fotos_ok:
            resultado = "# Fotos listas para Instagram\n\n"
            for f in fotos_ok:
                resultado += f"## {f['archivo']}\n"
                resultado += f"- Categoria: {f['categoria']}\n"
                resultado += f"- Caption: {f['caption']}\n\n"
            self.save_result(resultado)

            msg_body = (f"{len(fotos_ok)} fotos procesadas y listas. "
                       f"Ver: agentes/agt01_visual/_resultado.md")
            self.send_message('agt02_instagram', 'Fotos disponibles para posts', msg_body)
            self.send_message('orchestrator', 'Fotos Instagram listas',
                f'{len(fotos_ok)} fotos de Africa aptas para publicacion.')
            self.notify(f"Fotos listas: {len(fotos_ok)} procesadas para Instagram")
        else:
            self.log.info("Sin fotos nuevas que procesar")
            memoria = self.get_memory()
            if not memoria:
                self.save_memory(
                    "Estado inicial: esperando fotos de Africa.\n"
                    "Brief enviado con 7 shots prioritarios."
                )

        self.log.info("AGT-01 completado")


if __name__ == '__main__':
    VisualAgent().run()
