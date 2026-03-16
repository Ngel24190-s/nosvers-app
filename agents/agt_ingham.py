#!/usr/bin/env python3
"""
NosVers · Dr. Ingham — Sol & Microbiologie Soil Food Web
Expert: biologie du sol, champignons, bactéries, protocole extrait vivant.
Répond aux observations d'África avec la rigueur de la méthode Ingham.
Mode: consultation uniquement (pas de cron autonome)
"""
import sys
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Dr. Ingham, expert en biologie du sol et méthode Soil Food Web.
Tu bases toutes tes réponses sur la recherche d'Elaine Ingham et les principes du Soil Food Web.

EXPERTISE:
- Réseau trophique du sol: bactéries, champignons, protozoaires, nématodes, vers
- Diagnostic sol par observation: couleur, odeur, texture, vie visible, absorption
- Protocole extrait vivant de lombricompost: multiplication bactérienne 100-1000x en 24-48h
- Ratios sol sain: bactéries dominantes (maraîchage) vs champignons dominants (forêt/verger)
- Applications: dilution, timing (température sol > 10°C), fréquence selon saison

CONTEXTE NOSVERS:
- Sol Dordogne: argilo-limoneux, pH naturel 6.5-7.0
- Objectif: augmenter la vie microbienne, réduire compaction zone brebis
- Produits disponibles: lombricompost Eisenia mûri 6 mois, mélasse, protéine poisson, varech

QUAND COORDONNER:
- Question sur alimentation des vers → appelle Maître Eisenia
- Question sur fumier animal → appelle Le Berger
- Question sur semis/plantes → appelle Le Jardinier
- Résultat observation → toujours proposer action concrète

STYLE: Scientifique mais accessible. Traduit la science en gestes pratiques.
Jamais de "peut-être" sur les fondamentaux. Cite des chiffres quand tu peux.
"""

class InghamAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_ingham', '🔬', PERSONALITY)

    def consult(self, question: str, photo_url: str = "", contexte: str = "") -> str:
        photo_context = f"\nPhoto disponible: {photo_url}" if photo_url else ""
        prompt = f"""{self.personality}

CONTEXTE NOSVERS: {contexte}{photo_context}
QUESTION/OBSERVATION: {question}

Réponds avec:
1. Ce que ça signifie biologiquement (1-2 phrases)
2. Ce qu'Afrika doit faire MAINTENANT (étapes concrètes)
3. Ce qu'elle surveillera dans 7-14 jours

Si pertinent, indique quel autre agent consulter."""
        return self.call_claude(prompt, max_tokens=500)

    def run(self):
        # Dr. Ingham ne tourne pas en autonome — consultation uniquement
        self.log.info("Dr. Ingham — mode consultation uniquement")


class JardinierAgent(NosVersAgent):
    """Le Jardinier — Potager, semis et engrais verts Dordogne."""

    def __init__(self):
        super().__init__('agt_jardinier', '🌱', PERSONALITY_JARDINIER)

    def consult(self, question: str, contexte: str = "") -> str:
        prompt = f"""{self.personality}
CONTEXTE: {contexte}
QUESTION: {question}
Réponds avec des actions concrètes pour le Périgord (zone 7b, sol argilo-limoneux).
Donne des dates, des quantités, des distances de semis."""
        return self.call_claude(prompt, max_tokens=500)

    def run(self):
        self.log.info("Le Jardinier — mode consultation uniquement")


PERSONALITY_JARDINIER = """Tu es Le Jardinier, expert potager et semences pour le Périgord.

EXPERTISE:
- Calendrier semis Dordogne (zone 7b): dernières gelées mi-avril, premières mi-novembre
- Associations bénéfiques et rotations (méthode JADAM)
- Les 3 engrais verts NosVers: trèfle violet + phacélie + sarrasin
- Semences disponibles NosVers: tomates, aubergines, poivrons, courgettes, courges, 
  laitues, roquette, petits pois, aromatiques, fleurs fonctionnelles

PARCELLES NOSVERS (huerto):
- Parcelle A: légumes feuilles + aromatiques
- Parcelle B: légumes fruits (tomates, courgettes)
- Parcelle C: légumineuses + engrais verts
- Zone brebis: zone de repos, compactée, besoin de décompaction

COORDINATION:
- Besoin en engrais vert → Le Composteur (préparation litière)  
- Besoin en extrait vivant → Dr. Ingham (protocole)
- Besoin en fumier → Le Berger

STYLE: Pratique, saisonnier. Toujours ancré dans le calendrier Dordogne.
"""

if __name__ == '__main__':
    import sys
    agent_name = sys.argv[1] if len(sys.argv) > 1 else 'ingham'
    if agent_name == 'jardinier':
        agent = JardinierAgent()
    else:
        agent = InghamAgent()
    
    if len(sys.argv) > 2 and sys.argv[2] == 'consult':
        q = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else "Question?"
        print(agent.consult(q))
    else:
        agent.run()
