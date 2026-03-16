#!/usr/bin/env python3
"""
NosVers · Le Berger — Spécialiste Animaux Intégrés
Expert: poules, canards, lapines, brebis Cameroun. Cycle intégré ferme.
Surveille les cycles reproductifs et déclenche les alertes automatiques.
Cron: toutes les 6h — 15 */6 * * *
"""
import sys, json
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Le Berger, expert en élevage intégré de NosVers.

EXPERTISE:
- Poules pondeuses: alimentation (120g/j céréale+légumineuse+minéral), santé, ponte
- Canards: cohabitation, alimentation, ponte saisonnière
- Lapines: cycles reproductifs (gestation 31j, sevrage J28-35), alimentation (600g/j x3)
- Brebis Cameroun: besoins saisonniers, agnelage, fumier de qualité
- CYCLE INTÉGRÉ: deyections → lombricompost → sol → production → nourriture animaux

LAPINES NOSVERS (état connu):
- Lapine Blanche: en production, surveiller sevrage
- Lapine Grise: en production
- Lapine Noire: en production
- Gestations durée: 31 jours. Sevrage: J28-35. Cubrición possible: 14j post-sevrage.

CASCADES QUE TU DÉCLENCHES:
- Sevrage imminent (J25+) → Tâche urgente pour África + préparer cage séparation
- Cubrición possible → Rappel África (optionnel, elle décide)
- Stock aliment critique → Alerte Angel
- Ponte faible → Diagnostic + alerte si persistant

STYLE: Bienveillant mais précis. Donne des délais clairs.
Quand sevrage urgent: tone d'alerte claire, étapes simples.
"""

CYCLES_LAPINES = {
    'gestation_jours': 31,
    'sevrage_min_jours': 28,
    'sevrage_max_jours': 35,
    'repos_post_sevrage': 7,
    'delai_cubricion_post_sevrage': 14,
}

class BergerAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_berger', '🐓', PERSONALITY)

    def get_animaux_status(self) -> dict:
        raw = self.vault_read('agentes/agt_berger', '_etat_animaux')
        if not raw:
            return {}
        try:
            import re as _re
            jm = _re.search(r'\{[\s\S]+\}', raw)
            return json.loads(jm.group()) if jm else {}
        except:
            return {}

    def check_lapines(self, animaux: dict) -> list:
        """Détecter les événements reproductifs des lapines."""
        events = []
        lapines = animaux.get('lapines', [])

        for lapine in lapines:
            nom = lapine.get('nom', '?')
            jour_mise_bas = lapine.get('jour_mise_bas')
            nb_petits = lapine.get('nb_petits', 0)

            if not jour_mise_bas:
                continue

            try:
                date_mb = datetime.strptime(jour_mise_bas, '%Y-%m-%d')
                jours_depuis = (datetime.now() - date_mb).days
            except:
                continue

            # Sevrage imminent (J25-35)
            if 25 <= jours_depuis <= 35:
                urgence = 'rouge' if jours_depuis >= 31 else 'orange'
                events.append({
                    'type': 'sevrage',
                    'lapine': nom,
                    'jour': jours_depuis,
                    'nb_petits': nb_petits,
                    'urgence': urgence,
                    'action': f"Séparer les {nb_petits} petits de {nom} — Jour {jours_depuis}/35"
                })

            # Sevrage dépassé (>35j)
            elif jours_depuis > 35:
                events.append({
                    'type': 'sevrage_urgent',
                    'lapine': nom,
                    'jour': jours_depuis,
                    'urgence': 'rouge',
                    'action': f"⚠️ SEVRAGE DÉPASSÉ — {nom} Jour {jours_depuis}. Séparer immédiatement."
                })

            # Cubrición possible (J42-60 post-mise bas = J14-28 post-sevrage)
            elif 42 <= jours_depuis <= 60:
                events.append({
                    'type': 'cubricion_possible',
                    'lapine': nom,
                    'jour': jours_depuis,
                    'urgence': 'jaune',
                    'action': f"Saillie possible pour {nom} (si tu veux relancer)"
                })

        return events

    def check_stock_aliment(self, animaux: dict) -> list:
        """Vérifier les stocks d'aliment."""
        alerts = []
        stocks = animaux.get('stocks_aliment', {})

        seuils = {
            'poules_kg': 3,    # 3j de réserve minimum
            'lapines_kg': 5,
            'brebis_kg': 10,
        }

        for animal, seuil in seuils.items():
            stock = stocks.get(animal, 999)
            if stock < seuil:
                alerts.append({
                    'type': 'stock_critique',
                    'animal': animal,
                    'stock_kg': stock,
                    'seuil_kg': seuil,
                    'urgence': 'rouge' if stock < seuil/2 else 'orange'
                })
        return alerts

    def run(self):
        self.log.info("Le Berger — vérification animaux")
        animaux = self.get_animaux_status()

        if not animaux:
            self.log.info("Pas de données animaux — mode consultation uniquement")
            return

        all_events = []
        all_events.extend(self.check_lapines(animaux))
        all_events.extend(self.check_stock_aliment(animaux))

        if not all_events:
            self.log.info("Animaux en ordre — aucun événement")
            return

        # Envoyer les événements au Planificateur
        for ev in all_events:
            if ev['urgence'] in ('rouge', 'orange'):
                msg = f"""ÉVÉNEMENT ANIMAL — {ev['type']}
Source: Le Berger
Urgence: {ev['urgence'].upper()}
Détail: {ev.get('action', ev.get('type','?'))}
Date: {datetime.now().strftime('%d/%m/%Y')}"""
                self.message_agent('agt_planificateur', msg)

                # Telegram direct si rouge
                if ev['urgence'] == 'rouge':
                    self.notify_telegram(
                        f"🐓 *Le Berger* — URGENT\n{ev['action']}"
                    )

        self.log.info(f"{len(all_events)} événements traités")

    def consult(self, question: str, contexte: str = "") -> str:
        animaux = self.get_animaux_status()
        prompt = f"""{self.personality}

ÉTAT DES ANIMAUX: {json.dumps(animaux, ensure_ascii=False) if animaux else 'Non disponible'}
CONTEXTE: {contexte}
QUESTION: {question}

Réponds de façon pratique. Donne des délais, des quantités, des étapes.
Si le fumier des animaux est pertinent pour les bacs, mentionne-le.
"""
        return self.call_claude(prompt, max_tokens=500)


if __name__ == '__main__':
    agent = BergerAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "État des animaux?"
        print(agent.consult(q))
    else:
        agent.run()
