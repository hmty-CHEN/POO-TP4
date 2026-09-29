"""Une plante validée et sa représentation textuelle / JSON."""
from __future__ import annotations

from donnees import nettoyer_plante


class Plante:
    """Regrouper les caractéristiques botaniques d'une plante."""

    def __init__(self, nom: str, nom_scientifique: str, famille: str,
                 cycle: str, besoins: list[str], photo: str | None):
        donnees = nettoyer_plante(dict(nom=nom, nom_scientifique=nom_scientifique,
                                      famille=famille, cycle=cycle,
                                      besoins=besoins, photo=photo))
        self.nom: str = donnees["nom"]
        self.nom_scientifique: str = donnees["nom_scientifique"]
        self.famille: str = donnees["famille"]
        self.cycle: str = donnees["cycle"]
        self.besoins: list[str] = donnees["besoins"]
        self.photo: str | None = donnees["photo"]

    def __str__(self) -> str:
        return (f"{self.nom} ({self.nom_scientifique}) — {self.famille}\n"
                f"Cycle : {self.cycle}\nBesoins : {', '.join(self.besoins)}\n"
                f"Photo : {self.photo or 'absente'}")

    def vers_dict(self) -> dict:
        return dict(nom=self.nom, nom_scientifique=self.nom_scientifique,
                    famille=self.famille, cycle=self.cycle,
                    besoins=list(self.besoins), photo=self.photo)


if __name__ == "__main__":
    for plante in (Plante("Tomate", "Solanum lycopersicum", "Solanaceae", "annuel", ["soleil"], "tomate.jpg"),
                   Plante("Menthe", "Mentha sp.", "Lamiaceae", "vivace", ["mi-ombre"], None),
                   Plante("Pois", "Pisum sativum", "Fabaceae", "annuel", ["soleil"], "pois.jpg")):
        print(plante, end="\n\n")
