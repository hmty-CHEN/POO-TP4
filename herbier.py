"""Collection de plantes, recherches et persistance JSON."""
from __future__ import annotations

import json
from pathlib import Path

from donnees import cle, detecter_doublons, nettoyer_plante, normaliser_besoin, normaliser_famille
from plante import Plante


class Herbier:
    """Index par nom scientifique ; copies défensives pour préserver l'index."""

    def __init__(self):
        self._plantes: dict[str, Plante] = {}

    @property
    def plantes(self) -> list[Plante]:
        return [Plante(**p.vers_dict()) for p in self._plantes.values()]

    def ajouter_plante(self, plante: Plante) -> None:
        if not isinstance(plante, Plante):
            raise TypeError("Un objet Plante est attendu.")
        copie = Plante(**plante.vers_dict())
        nom = cle(copie.nom_scientifique)
        if nom in self._plantes:
            raise ValueError(f"Doublon : {copie.nom_scientifique}")
        self._plantes[nom] = copie

    def supprimer_plante(self, nom_scientifique: str) -> None:
        nom = cle(nom_scientifique)
        if nom not in self._plantes:
            raise ValueError(f"Plante inconnue : {nom_scientifique}")
        del self._plantes[nom]

    def rechercher_scientifique(self, nom: str) -> Plante | None:
        plante = self._plantes.get(cle(nom))
        return Plante(**plante.vers_dict()) if plante else None

    def rechercher(self, nom: str) -> list[Plante]:
        return [p for p in self.plantes if cle(nom) in cle(p.nom)]

    def filtrer(self, famille=None, cycle=None, besoin=None) -> list[Plante]:
        return [p for p in self.plantes
                if (famille is None or p.famille == normaliser_famille(famille))
                and (cycle is None or p.cycle == cle(cycle))
                and (besoin is None or normaliser_besoin(besoin) in p.besoins)]

    def filtrer_par_famille(self, famille: str) -> list[Plante]:
        return self.filtrer(famille=famille)

    def filtrer_par_cycle(self, cycle: str) -> list[Plante]:
        return self.filtrer(cycle=cycle)

    def filtrer_par_besoin(self, besoin: str) -> list[Plante]:
        return self.filtrer(besoin=besoin)

    def afficher(self, plantes=None) -> None:
        selection = self.plantes if plantes is None else plantes
        print("\n\n".join(map(str, selection)) or "Aucune plante trouvée.")

    def sauvegarder_json(self, nom_fichier) -> None:
        contenu = [nettoyer_plante(p.vers_dict()) for p in self._plantes.values()]
        Path(nom_fichier).write_text(json.dumps(contenu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def charger_json(self, nom_fichier) -> dict:
        """Remplacer la collection seulement après lecture et analyse réussies."""
        donnees = json.loads(Path(nom_fichier).read_text(encoding="utf-8"))
        if not isinstance(donnees, list):
            raise ValueError("La racine JSON doit être une liste.")
        rapport = {"lus": len(donnees), "acceptes": 0, "erreurs": [],
                   "doublons": detecter_doublons(donnees), "ignores": [],
                   "corrections": [], "photos_absentes": []}
        nouveau = Herbier()
        for position, brute in enumerate(donnees, 1):
            try:
                propre = nettoyer_plante(brute)
            except ValueError as erreur:
                rapport["erreurs"].append({"ligne": position, "message": str(erreur)})
                continue
            if propre != brute:
                rapport["corrections"].append(position)
            if not propre["photo"]:
                rapport["photos_absentes"].append(position)
            if cle(propre["nom_scientifique"]) in nouveau._plantes:
                rapport["ignores"].append(position)
                continue
            nouveau.ajouter_plante(Plante(**propre))
        if donnees and not nouveau._plantes:
            raise ValueError("Aucune entrée valide ; herbier conservé. " + str(rapport["erreurs"]))
        self._plantes = nouveau._plantes
        rapport["acceptes"] = len(self._plantes)
        return rapport
