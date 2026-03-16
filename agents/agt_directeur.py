#!/usr/bin/env python3
"""
NosVers · Le Directeur — Stratégie Éditoriale & Brief Hebdomadaire
Vue complète sur le calendrier, le stock et les agents.
Génère le brief du dimanche. Coordonne La Plume et L'Œil.
Cron: dimanche 9h — 0 9 * * 0
"""
import sys, json
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Le Directeur, stratège éditorial de NosVers.

RÔLE:
- Tu as la vue globale: stock produits, saison, actualité ferme, performances Instagram
- Chaque dimanche tu génères un brief de 3 posts pour la semaine
- Tu sais quoi pousser, quand, et pourquoi
- Tu coordonnes La Plume (textes) et L'Œil (visuels)

RÈGLES ÉDITORIALES NOSVERS:
- 3 posts/semaine — lundi, mercredi, vendredi ou samedi
- Alternance: 1 éducatif (sol/technique) + 1 produit + 1 ferme/vie
- Jamais deux posts produit consécutifs
- Ton: authentique, technique, ancré dans la ferme réelle
- Saison actuelle: mars → semis, préparation sol, extrait vivant actif

PRODUITS À POUSSER (par priorité):
1. Pack Engrais Vert (9,90€) — saison printemps
2. Kit Extrait Vivant (45€) — haute saison mars-octobre
3. Service Frais (25€) — commandes locales
4. Atelier Sol Vivant (85€) — dates printemps

MÉTRIQUES QUE TU UTILISES (si disponibles via L'Analyste):
- Post le plus performant de la semaine → type à répéter
- Heure de publication optimale → généralement 19h-21h
- Hashtags performants → sol vivant, lombricompost, dordogne

STYLE: Stratégique, décisif, court. Brief = actionnable immédiatement.
"""

class DirecteurAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_directeur', '🎯', PERSONALITY)

    def get_analytics_summary(self) -> str:
        raw = self.vault_read('agentes/agt11_analytics', '_resultado')
        return raw[:500] if raw else "Pas encore de données analytics disponibles."

    def get_ferme_actus(self) -> str:
        """Lire les événements récents de la ferme pour le brief."""
        eisenia = self.vault_read('agentes/agt_eisenia', '_etat_bacs')
        berger = self.vault_read('agentes/agt_berger', '_etat_animaux')
        journal = self.vault_read('agentes/orchestrator', '_memoria')
        actu = ""
        if eisenia:
            actu += f"BACS: {eisenia[:200]}\n"
        if berger:
            actu += f"ANIMAUX: {berger[:200]}\n"
        return actu or "Aucune actualité récente disponible."

    def generate_brief(self) -> str:
        analytics = self.get_analytics_summary()
        ferme = self.get_ferme_actus()
        semaine_num = datetime.now().isocalendar()[1]
        lundi = datetime.now() + timedelta(days=(7 - datetime.now().weekday()))

        prompt = f"""{self.personality}

SEMAINE: {semaine_num} — du {lundi.strftime('%d/%m')} au {(lundi+timedelta(6)).strftime('%d/%m')}
SAISON: Mars — printemps, semis en cours, sol actif

ACTUALITÉS FERME:
{ferme}

PERFORMANCES RÉCENTES:
{analytics}

Génère le brief de 3 posts pour la semaine au format:

POST 1 — [LUNDI] — [Type: éducatif|produit|ferme]
Angle: ...
Message clé (1 phrase): ...
CTA: ...
Agent à briefer: La Plume + L'Œil

POST 2 — [MERCREDI] — [Type: éducatif|produit|ferme]
Angle: ...
Message clé (1 phrase): ...
CTA: ...
Agent à briefer: La Plume

POST 3 — [VENDREDI] — [Type: éducatif|produit|ferme]
Angle: ...
Message clé (1 phrase): ...
CTA: ...
Agent à briefer: La Plume + L'Œil

PRIORITÉ PRODUIT CETTE SEMAINE: [produit + raison]

Sois concret et ancré dans ce qui se passe réellement à NosVers cette semaine."""

        return self.call_claude(prompt, max_tokens=700)

    def dispatch_to_agents(self, brief: str):
        """Envoyer le brief à La Plume et L'Œil."""
        msg_plume = f"""BRIEF SEMAINE — DE LE DIRECTEUR
Date: {datetime.now().strftime('%d/%m/%Y')}

{brief}

ACTION: Rédiger les 3 captions selon ce brief.
Format attendu: caption Instagram + hashtags (max 30) + note pour L'Œil si photo nécessaire.
"""
        self.message_agent('agt02_instagram', msg_plume)

        msg_oeil = f"""BRIEF VISUELS — DE LE DIRECTEUR
Date: {datetime.now().strftime('%d/%m/%Y')}

{brief}

ACTION: Identifier les photos disponibles dans Drive pour les posts avec L'Œil.
Sélectionner 1-2 photos par post visuel. Signaler si aucune photo disponible.
"""
        self.message_agent('agt01_visual', msg_oeil)
        self.log.info("Brief dispatché à La Plume et L'Œil")

    def run(self):
        self.log.info("Le Directeur — génération brief hebdomadaire")
        brief = self.generate_brief()
        self.save_result(brief)
        self.dispatch_to_agents(brief)

        # Telegram résumé pour Angel
        lines = [l for l in brief.split('\n') if l.startswith('POST') or 'PRIORITÉ' in l]
        summary = '\n'.join(lines[:8])
        self.notify_telegram(
            f"🎯 *Brief semaine — Le Directeur*\n\n{summary}\n\nBrief complet envoyé à La Plume et L'Œil."
        )
        self.log.info("Brief hebdomadaire terminé")

    def consult(self, question: str, contexte: str = "") -> str:
        prompt = f"""{self.personality}
CONTEXTE: {contexte}
QUESTION STRATÉGIQUE: {question}
Réponds avec une recommandation claire et actionnaire."""
        return self.call_claude(prompt, max_tokens=400)


if __name__ == '__main__':
    agent = DirecteurAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Que publier cette semaine?"
        print(agent.consult(q))
    else:
        agent.run()
