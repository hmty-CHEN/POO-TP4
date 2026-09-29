"""Questions distinctes et quatre familles différentes par question."""
from __future__ import annotations

import random

from herbier import Herbier
from question import Question


class Quiz:
    def __init__(self, herbier: Herbier):
        self.herbier: Herbier = herbier
        self.questions: list[Question] = []
        self.reponses: list[str] = []

    def preparer(self, nombre: int = 5, famille: str | None = None) -> list[Question]:
        if not isinstance(nombre, int) or nombre <= 0:
            raise ValueError("Le nombre de questions doit être positif.")
        plantes = self.herbier.filtrer(famille=famille)
        familles = sorted({p.famille for p in self.herbier.plantes})
        if not plantes:
            raise ValueError("Aucune plante disponible pour ce quiz.")
        if len(familles) < 4:
            raise ValueError("Il faut au moins quatre familles dans l'herbier pour quatre propositions.")
        self.questions = []
        self.reponses = []
        for plante in random.sample(plantes, min(nombre, len(plantes))):
            choix = [plante.famille] + random.sample([f for f in familles if f != plante.famille], 3)
            random.shuffle(choix)
            self.questions.append(Question(plante, choix))
        return list(self.questions)

    def repondre(self, reponse: str) -> bool:
        if len(self.reponses) >= len(self.questions):
            raise ValueError("Le quiz est terminé ou n'a pas commencé.")
        correcte = self.questions[len(self.reponses)].verifier(reponse)
        self.reponses.append(reponse.strip().upper())
        return correcte

    def resultat(self) -> dict:
        score = sum(q.verifier(r) for q, r in zip(self.questions, self.reponses))
        total = len(self.questions)
        pourcentage = 100 * score / total if total else 0
        appreciation = ("Excellent !" if pourcentage == 100 else
                        "Très bien !" if pourcentage >= 80 else
                        "Bien, mais encore un peu de révision." if pourcentage >= 60 else
                        "Revoir les familles botaniques.")
        return dict(score=score, total=total, pourcentage=pourcentage, appreciation=appreciation)
