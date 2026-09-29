"""Une question botanique et la vérification de sa réponse."""
from __future__ import annotations

from plante import Plante


class Question:
    def __init__(self, plante: Plante, choix: list[str]):
        self.plante: Plante = plante
        self.choix: list[str] = choix

    def verifier(self, reponse: str) -> bool:
        numero = reponse.strip()
        if numero not in ("1", "2", "3", "4"):
            raise ValueError("Répondre 1, 2, 3 ou 4.")
        return self.choix[int(numero) - 1] == self.plante.famille
