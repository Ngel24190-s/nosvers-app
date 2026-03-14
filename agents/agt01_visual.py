#!/usr/bin/env python3
"""
NosVers · AGT-01 Visual — "El Ojo"
Procesa fotos: local + Drive → analiza con Claude Vision → clasifica para Instagram/Blog
Cron: manual (activado por orchestrator o cuando hay fotos nuevas)
"""
import sys, os, base64, json, re
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent, CLAUDE_KEY
from pathlib import Path
import requests as req
from dotenv import load_dotenv
load_dotenv('/home/nosvers/.env')

PERSONALITY = """PERSONALIDAD — AGT-01 "El Ojo"
Obsesionado con la luz natural y la tierra visible.
Ves una foto y en 3 segundos sabes si vale o no.
No procesas basura — si la foto no tiene potencial, lo dices sin rodeos.
Conoces la identidad visual de Nerea de memoria.
Hablas como un fotógrafo de campo. Concreto y visual.
Tono: Artesanal. Preciso. Con criterio estético claro.
Paleta NosVers: blanco cálido #FEFAF4, verde vivo #5A7A2E.
REGLA: Nunca publiques sin aprobación de Angel."""

DRIVE_FOLDERS = {
    'instagram': os.getenv('DRIVE_FOLDER_INSTAGRAM', ''),
    'vers-compost': os.getenv('DRIVE_FOLDER_VERS', ''),
    'huerto': os.getenv('DRIVE_FOLDER_HUERTO', ''),
    'general': os.getenv('DRIVE_FOLDER_GENERAL', ''),
}

class VisualAgent(NosVersAgent):
    UPLOADS = Path('/home/nosvers/uploads')
    INSTAGRAM = Path('/home/nosvers/uploads/instagram')
    SYNCED = Path('/home/nosvers/logs/agt01_processed.txt')

    def __init__(self):
        super().__init__('agt01_visual', '📷', PERSONALITY)
        self.UPLOADS.mkdir(parents=True, exist_ok=True)
        self.INSTAGRAM.mkdir(parents=True, exist_ok=True)

    def get_processed(self):
        if self.SYNCED.exists():
            return set(self.SYNCED.read_text().strip().splitlines())
        return set()

    def mark_processed(self, name):
        self.SYNCED.parent.mkdir(parents=True, exist_ok=True)
        with open(self.SYNCED, 'a') as f:
            f.write(name + '\n')

    def list_drive_files(self, folder_id):
        """Lista imágenes de carpeta pública Drive."""
        if not folder_id:
            return []
        try:
            url = "https://www.googleapis.com/drive/v3/files"
            params = {
                'q': f"'{folder_id}' in parents and mimeType contains 'image/'",
                'fields': 'files(id,name,mimeType)',
                'orderBy': 'createdTime desc',
                'pageSize': 10,
            }
            r = req.get(url, params=params, timeout=15)
            return r.json().get('files', []) if r.status_code == 200 else []
        except:
            return []

    def download_drive(self, file_id, filename, category):
        """Descarga imagen de Drive."""
        dest_dir = self.UPLOADS / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / filename
        if dest.exists():
            return dest
        try:
            r = req.get(f"https://drive.google.com/uc?export=download&id={file_id}", timeout=30, stream=True)
            if r.status_code == 200:
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return dest
        except:
            pass
        return None

    def analyze_photo(self, foto_path):
        """Analiza foto con Claude Vision."""
        if not CLAUDE_KEY:
            return {"apta_instagram": False, "categoria": "general", "descripcion": "Sin API key"}
        
        try:
            with open(foto_path, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            prompt = """Analiza esta foto para NosVers (ferme lombricole, Dordogne).
Responde SOLO en JSON:
{
  "apta_instagram": true/false,
  "apta_blog": true/false,
  "categoria": "vers-compost" | "huerto" | "ferme" | "producto" | "general",
  "luz": "buena" | "aceptable" | "mala",
  "composicion": "buena" | "aceptable" | "mala",
  "elementos": ["lista de lo que ves"],
  "caption_fr": "caption sugerida en francés si es apta para Instagram",
  "ajustes": "ajustes técnicos recomendados",
  "razon": "por qué sí o no para Instagram"
}"""
            
            r = req.post('https://api.anthropic.com/v1/messages',
                headers={'x-api-key': CLAUDE_KEY, 'anthropic-version': '2023-06-01',
                         'Content-Type': 'application/json'},
                json={'model': 'claude-sonnet-4-6', 'max_tokens': 500,
                      'messages': [{'role': 'user', 'content': [
                          {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/jpeg', 'data': img_b64}},
                          {'type': 'text', 'text': prompt}
                      ]}]},
                timeout=45)
            
            text = r.json()['content'][0]['text']
            clean = re.sub(r'```json|```', '', text).strip()
            return json.loads(clean)
        except Exception as e:
            self.log.error(f"Error analizando {foto_path.name}: {e}")
            return {"apta_instagram": False, "categoria": "general", "descripcion": str(e)}

    def scan_local_photos(self):
        """Busca fotos nuevas en uploads/ (subidas por África o Angel)."""
        processed = self.get_processed()
        fotos = []
        for ext in ('*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG'):
            fotos += list(self.UPLOADS.rglob(ext))
        return [f for f in fotos if f.name not in processed and 'visuels' not in str(f)]

    def scan_drive_photos(self):
        """Busca fotos nuevas en carpetas Drive."""
        processed = self.get_processed()
        nuevas = []
        for category, folder_id in DRIVE_FOLDERS.items():
            if not folder_id:
                continue
            files = self.list_drive_files(folder_id)
            for f in files:
                key = f"drive_{f['id']}"
                if key not in processed:
                    nuevas.append({'id': f['id'], 'name': f['name'], 'category': category, 'key': key})
        return nuevas

    def run(self):
        self.log.info("AGT-01 Visual iniciando")
        resultados = []

        # 1. Fotos locales
        locales = self.scan_local_photos()
        self.log.info(f"Fotos locales nuevas: {len(locales)}")
        
        for foto in locales[:5]:  # Máximo 5 por ejecución
            self.log.info(f"Analizando local: {foto.name}")
            analysis = self.analyze_photo(foto)
            
            if analysis.get('apta_instagram'):
                # Copiar a carpeta instagram
                import shutil
                dest = self.INSTAGRAM / foto.name
                shutil.copy2(foto, dest)
                self.log.info(f"→ Instagram: {foto.name}")
            
            resultados.append(f"📷 {foto.name}: {'✅ IG' if analysis.get('apta_instagram') else '—'} | {analysis.get('categoria','?')} | {analysis.get('luz','?')}")
            self.mark_processed(foto.name)

        # 2. Fotos Drive
        drive_nuevas = self.scan_drive_photos()
        self.log.info(f"Fotos Drive nuevas: {len(drive_nuevas)}")
        
        for item in drive_nuevas[:5]:
            self.log.info(f"Descargando Drive: {item['name']} ({item['category']})")
            local = self.download_drive(item['id'], item['name'], item['category'])
            
            if local and local.exists() and local.stat().st_size > 1000:
                analysis = self.analyze_photo(local)
                
                if analysis.get('apta_instagram'):
                    import shutil
                    shutil.copy2(local, self.INSTAGRAM / local.name)
                    self.log.info(f"→ Instagram: {local.name}")
                
                resultados.append(f"📷 {item['name']} (Drive/{item['category']}): {'✅ IG' if analysis.get('apta_instagram') else '—'} | {analysis.get('categoria','?')}")
            else:
                resultados.append(f"📷 {item['name']}: ⚠️ descarga fallida o muy pequeño")
            
            self.mark_processed(item['key'])

        # 3. Guardar resultado
        if resultados:
            resumen = f"# AGT-01 Visual — {self.ts}\n\n" + '\n'.join(resultados)
            resumen += f"\n\nTotal: {len(locales)} locales + {len(drive_nuevas)} Drive"
            self.save_result(resumen)
            self.save_memory(f"Última ejecución: {self.ts}. {len(resultados)} fotos procesadas.")
            
            # Notificar a Angel si hay fotos para Instagram
            ig_count = sum(1 for r in resultados if '✅ IG' in r)
            if ig_count > 0:
                self.notify(f"📷 AGT-01 Visual: {ig_count} foto(s) lista(s) para Instagram.\n{chr(10).join(r for r in resultados if '✅ IG' in r)}")
        else:
            self.log.info("Sin fotos nuevas para procesar")
            self.save_memory(f"Última ejecución: {self.ts}. Sin fotos nuevas.")

        self.log.info("AGT-01 Visual completado")

if __name__ == '__main__':
    VisualAgent().run()
