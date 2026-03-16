#!/usr/bin/env python3
"""
NosVers · Le Composteur — Spécialiste Compost & Alimentation Bacs
Expert: andains, ratios C/N, alimentation des vers, préparation litière.
Reçoit les notifications d'Eisenia et prépare les ressources en conséquence.
Cron: toutes les 6h — 30 */6 * * *
"""
import sys, json
from datetime import datetime
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Le Composteur, expert compost et alimentation des lombrics de NosVers.

EXPERTISE ABSOLUE:
- Ratios C/N: calcul, correction, équilibre
- Matières disponibles à NosVers: fumier poules, fumier lapins, fumier brebis, feuilles, paille, carton
- Préparation litière pour nouveaux bacs
- Préparation alimentaire pour les vers: ce qui accélère, ce qui freine
- Compostage andains: température, retournement, maturité
- RÈGLE ABSOLUE: jamais de fumier poule cru aux vers — toujours pré-composté minimum 3 semaines

RESSOURCES NOSVERS DISPONIBLES:
- Fumier poule: riche en N, pré-composter obligatoire
- Fumier lapin: équilibré, excellent C/N, peut aller directement
- Fumier brebis Cameroun: riche, modéré, pré-composter recommandé
- Carton non imprimé: excellent C, base litière
- Feuilles mortes: bon C, sécher avant utilisation
- Paille: C élevé, bon pour équilibre

CASCADES QUE TU DÉCLENCHES:
- Litière prête → Notifier Maître Eisenia + créer tâche África
- Stock faible d'un matériau → Alerte Angel (commander)
- Compost mûr disponible → Notifier L'Analyste (mise à jour stock)

STYLE: Pratique, précis, donne des quantités et des durées.
Quand tu reçois un message d'Eisenia: prépare un plan d'action concret pour África.
"""

class ComposteurAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_composteur', '🍂', PERSONALITY)

    def process_inbox(self):
        """Lire les messages reçus des autres agents."""
        inbox = self.vault_read('agentes/agt_composteur', '_inbox')
        if not inbox or not inbox.strip():
            return []
        messages = [m.strip() for m in inbox.split('---') if m.strip()]
        return messages

    def clear_inbox(self):
        self.vault_write('agentes/agt_composteur', '_inbox', '', modo='overwrite')

    def prepare_litiere_plan(self, bac: str, kg_lombricompost: float = 0) -> str:
        """Générer un plan de préparation litière pour un bac."""
        prompt = f"""{self.personality}

Le bac {bac} va être récolté/dupliqué dans les prochains jours.
Lombricompost à récolter: ~{kg_lombricompost}kg

Génère un plan de préparation litière CONCRET pour África:
- Quantités exactes de chaque matériau
- Ordre de préparation
- Temps nécessaire
- Points de contrôle
Format: liste étapes numérotées, court, actionnable."""
        return self.call_claude(prompt, max_tokens=400)

    def run(self):
        self.log.info("Le Composteur — lecture inbox")
        messages = self.process_inbox()

        if not messages:
            self.log.info("Inbox vide — aucune action requise")
            return

        for msg in messages:
            self.log.info(f"Message reçu: {msg[:80]}")

            # Détecter si c'est une notification récolte/duplication d'Eisenia
            if 'recolte_imminente' in msg or 'Bac' in msg and 'récolter' in msg:
                # Extraire le nom du bac
                import re
                bac_match = re.search(r'Bac #?\d+|IBC', msg)
                bac = bac_match.group() if bac_match else 'inconnu'
                kg_match = re.search(r'~?(\d+[\.,]?\d*)\s*kg', msg)
                kg = float(kg_match.group(1).replace(',', '.')) if kg_match else 0

                # Générer plan de préparation
                plan = self.prepare_litiere_plan(bac, kg)

                # Notifier África + créer tâche planificateur
                tache = f"""TÂCHE LITIÈRE — {bac}
Source: Le Composteur
Date: {datetime.now().strftime('%d/%m/%Y')}
Priorité: NORMALE

PLAN DE PRÉPARATION LITIÈRE:
{plan}

Confirme dans l'app quand c'est prêt."""
                self.message_agent('agt_planificateur', tache)

                # Telegram bref
                self.notify_telegram(
                    f"🍂 *Le Composteur*\n"
                    f"Litière pour {bac} programmée.\n"
                    f"Tâche ajoutée dans l'app pour África."
                )

                self.log.info(f"Plan litière créé pour {bac}")

        self.clear_inbox()
        self.log.info("Le Composteur — inbox traitée")

    def consult(self, question: str, contexte: str = "") -> str:
        prompt = f"""{self.personality}

CONTEXTE: {contexte}
QUESTION: {question}

Réponds de façon pratique. Donne des quantités, des ratios, des durées.
Si la question touche les vers (stress, fuite, duplication), coordonne avec Maître Eisenia.
"""
        return self.call_claude(prompt, max_tokens=500)


if __name__ == '__main__':
    agent = ComposteurAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "État du compost?"
        print(agent.consult(q))
    else:
        agent.run()
