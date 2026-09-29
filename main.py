"""Menu du TP : python3 main.py (Python 3.9+, bibliothèque standard)."""

import json
from pathlib import Path

from herbier import Herbier
from plante import Plante
from quiz import Quiz

DOSSIER = Path(__file__).resolve().parent / "data"


def afficher_rapport(rapport):
    print(f"{rapport['acceptes']} plantes acceptées sur {rapport['lus']} entrées.")
    for erreur in rapport["erreurs"]:
        print(f"Entrée {erreur['ligne']} rejetée : {erreur['message']}")
    print(f"Groupes de doublons : {rapport['doublons']}")
    print(f"Entrées répétées ignorées : {rapport['ignores']}")
    print(f"Entrées normalisées : {rapport['corrections']}")
    print(f"Photos absentes (acceptées) : {rapport['photos_absentes']}")


def ajouter(herbier):
    valeurs = [input(f"{label} : ") for label in
               ("Nom", "Nom scientifique", "Famille", "Cycle")]
    besoins = [b.strip() for b in input("Besoins séparés par des virgules : ").split(",") if b.strip()]
    photo = input("Photo (facultative) : ").strip() or None
    herbier.ajouter_plante(Plante(*valeurs, besoins, photo))
    print("Plante ajoutée.")


def lancer_quiz(herbier):
    familles = sorted({p.famille for p in herbier.plantes})
    print("Mode révision — 0. Toutes les familles")
    for numero, famille in enumerate(familles, 1):
        print(f"{numero}. {famille}")
    while True:
        try:
            choix = int(input("Famille : "))
            if not 0 <= choix <= len(familles):
                raise ValueError
            break
        except ValueError:
            print("Saisir un numéro de famille valide.")
    quiz = Quiz(herbier)
    questions = quiz.preparer(famille=familles[choix - 1] if choix else None)
    print(f"{len(questions)} questions, sans répétition.")
    for numero, question in enumerate(questions, 1):
        print(f"\n{numero}. Quelle est la famille botanique de {question.plante.nom} ?")
        for lettre, famille in zip("ABCD", question.choix):
            print(f"{lettre}. {famille}")
        while True:
            try:
                correcte = quiz.repondre(input("Réponse : "))
                break
            except ValueError as erreur:
                print(erreur)
        print("Bonne réponse !" if correcte else f"Mauvaise réponse. La bonne réponse était : {question.plante.famille}")
    resultat = quiz.resultat()
    print(f"\nRESULTAT\nScore : {resultat['score']} / {resultat['total']}\n"
          f"{resultat['pourcentage']:.0f} %\n{resultat['appreciation']}")


def chemin_saisi():
    chemin = Path(input("Fichier JSON (défaut : mon_herbier.json) : ").strip() or "mon_herbier.json").expanduser()
    return chemin if chemin.is_absolute() else DOSSIER / chemin


def main():
    herbier = Herbier()
    initial = DOSSIER / "mon_herbier.json"
    if not initial.exists():
        initial = DOSSIER / "plantes_degradees.json"
    try:
        afficher_rapport(herbier.charger_json(initial))
    except (OSError, ValueError) as erreur:
        print(f"Chargement initial impossible : {erreur}")
    while True:
        print("\n====================================\n         MON HERBIER NUMÉRIQUE\n====================================")
        print(f"{len(herbier.plantes)} plantes ; {len({p.famille for p in herbier.plantes})} familles")
        print("1. Afficher les plantes\n2. Rechercher une plante\n3. Filtrer par famille\n"
              "4. Filtrer par cycle\n5. Filtrer par besoin\n6. Ajouter une plante\n"
              "7. Supprimer une plante\n8. Sauvegarder l'herbier\n9. Charger l'herbier\n"
              "10. Lancer le quiz\n11. Filtrer par plusieurs critères\n0. Quitter")
        try:
            choix = int(input("Choix : "))
            if choix == 0:
                print("Au revoir ! Pensez à sauvegarder avec le choix 8 avant de quitter.")
                return
            if choix == 1:
                herbier.afficher()
            elif choix == 2:
                herbier.afficher(herbier.rechercher(input("Nom ou partie du nom : ")))
            elif choix in (3, 4, 5):
                methode = {3: herbier.filtrer_par_famille, 4: herbier.filtrer_par_cycle, 5: herbier.filtrer_par_besoin}[choix]
                herbier.afficher(methode(input("Valeur du filtre : ")))
            elif choix == 6:
                ajouter(herbier)
            elif choix == 7:
                herbier.supprimer_plante(input("Nom scientifique exact : "))
                print("Plante supprimée.")
            elif choix == 8:
                herbier.sauvegarder_json(chemin_saisi())
                print("Herbier sauvegardé.")
            elif choix == 9:
                afficher_rapport(herbier.charger_json(chemin_saisi()))
            elif choix == 10:
                lancer_quiz(herbier)
            elif choix == 11:
                filtres = {champ: input(f"{champ} (vide = tous) : ").strip() or None
                           for champ in ("famille", "cycle", "besoin")}
                herbier.afficher(herbier.filtrer(**filtres))
            else:
                print("Choix inconnu : saisir un nombre de 0 à 11.")
        except FileNotFoundError:
            print("Fichier JSON inexistant.")
        except json.JSONDecodeError as erreur:
            print(f"JSON mal formé, ligne {erreur.lineno}.")
        except (ValueError, TypeError) as erreur:
            print(f"Saisie ou données incorrectes : {erreur}")
        except OSError as erreur:
            print(f"Erreur de fichier : {erreur}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nFin de la session.")
