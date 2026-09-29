# Mon herbier numérique

Projet de programmation orientée objet en Python — **CHEN Qiyue**.

Application en ligne de commande pour gérer des fiches de plantes, rechercher
et filtrer une collection, sauvegarder les données en JSON et réviser les
familles botaniques avec un quiz sans répétition.

Le projet comprend le nettoyage et la validation du jeu fourni : **16 entrées
brutes donnent 13 plantes valides, réparties en 8 familles**.

## Environnement

- **Python 3.9 ou supérieur**.
- Bibliothèque standard uniquement : aucun paquet à installer avec `pip`.
- Un navigateur pour consulter le rapport et le diagramme UML.

## Installation et lancement

```bash
git clone https://github.com/hmty-CHEN/POO-TP4.git
cd POO-TP4
python3 main.py
```

Toutes les commandes ci-dessous s'exécutent à la racine du projet.
Sous Windows, remplacer `python3` par `python` ou `py` si nécessaire.

Le menu permet de consulter, ajouter et supprimer des plantes, de rechercher
par nom, de combiner des filtres et de lancer le quiz, éventuellement par famille.
Choisir **8** pour sauvegarder avant de quitter ; **9** charge un fichier et
remplace la collection courante. Les chemins JSON relatifs sont résolus dans
`data/` ; le fichier par défaut est `data/mon_herbier.json`.

## Structure du projet

```text
.
├── main.py                  # Menu et point d'entrée
├── plante.py                # Classe Plante
├── herbier.py               # Collection, recherche, filtres et JSON
├── donnees.py               # Nettoyage, validation et doublons
├── quiz.py                  # Préparation du quiz et calcul du score
├── question.py              # Choix proposés et vérification d'une réponse
├── data/                    # Données originales et nettoyées
├── docs/                    # Sujet, rapport et résultats
│   └── uml/                 # Diagramme exporté en HTML et SVG
├── tests/                   # Tests automatisés
├── tools/uml_live.py         # Génération et synchronisation du diagramme
└── .github/workflows/        # Vérifications automatiques sur GitHub
```

## Diagramme UML

```bash
python3 tools/uml_live.py
```

Ouvrir **http://127.0.0.1:8765** et laisser le serveur actif. Le diagramme est
généré à partir du code Python et se met à jour automatiquement après modification.
Arrêter le serveur avec `Ctrl+C`.

Pour produire uniquement les fichiers consultables hors ligne :

```bash
python3 tools/uml_live.py --export
```

## Tests et documentation

```bash
python3 -m unittest discover -v
```

Les 15 tests couvrent les recherches, les filtres, le nettoyage, la sauvegarde,
le quiz et les principaux cas d'erreur. GitHub Actions est configuré pour
Python 3.9, 3.12 et 3.13.

- [Rapport de réalisation — quatre pages A4](docs/rapport.html)
- [Bilan du nettoyage](docs/rapport_nettoyage.json)
- [Résultats des tests](docs/resultats_tests.txt)
- [Diagramme UML](docs/uml/uml.svg)

Pour lire le rapport mis en page, ouvrir `docs/rapport.html` dans un navigateur.
