"""Une question botanique et la vérification de sa réponse."""
from __future__ import annotations

from plante import Plante


class Question:
    def __init__(self, plante: Plante, choix: list[str]):
        self.plante: Plante = plante
        self.choix: list[str] = choix

    def verifier(self, reponse: str) -> bool:
        lettre = reponse.strip().upper()
        if lettre not in ("A", "B", "C", "D"):
            raise ValueError("Répondre A, B, C ou D.")
        return self.choix[ord(lettre) - ord("A")] == self.plante.famille
