# Mon herbier numérique

TP de programmation orientée objet en Python : collection de plantes, nettoyage
de données, recherche, filtres, persistance JSON et quiz botanique.

**Python 3.9+ · Bibliothèque standard uniquement · 15 tests automatisés**

## Démarrage

Depuis la racine du projet, après téléchargement ou clonage :

```bash
python3 main.py
```

Le menu permet d'afficher, rechercher, filtrer, ajouter, supprimer, sauvegarder,
charger et réviser les familles botaniques. Le choix 11 combine les critères avec ET.
Utiliser le choix **8** pour sauvegarder avant de quitter. Le choix **9** remplace
la collection courante après validation du fichier.

启动后通过菜单操作；退出前选择 **8** 保存。所有相对 JSON 路径基于 `data/`，
默认保存到 `data/mon_herbier.json`。个人数据可保存到 `data/local/`（自行建立该目录），
该目录由 Git 忽略。项目提供的原始数据与清洗后数据均应提交至 GitHub。

## Structure du dépôt

```text
.
├── .github/workflows/tests.yml  # Vérification à chaque push / pull request
├── .gitignore
├── README.md
├── main.py                     # Menu et point d'entrée
├── plante.py                   # Classe Plante
├── herbier.py                  # Collection et persistance
├── donnees.py                  # Nettoyage, validation, doublons
├── quiz.py                     # Classe Quiz : sélection et score
├── question.py                 # Classe Question : choix et vérification
├── data/
│   ├── plantes_degradees.json   # 16 entrées originales du sujet
│   └── mon_herbier.json         # 13 plantes valides, 8 familles
├── docs/
│   ├── sujet/TP Mon herbier.docx
│   ├── rapport.html            # Rapport en trois pages A4
│   ├── rapport_nettoyage.json  # Corrections, rejets et doublons
│   ├── resultats_tests.txt
│   └── uml/
│       ├── uml.html             # Diagramme autonome
│       └── uml.svg              # Export vectoriel
├── tests/
│   ├── __init__.py
│   └── test_herbier.py
└── tools/
    ├── __init__.py
    └── uml_live.py              # Génération AST et serveur local
```

Les modules métier restent à la racine, conformément à l'architecture du sujet,
pour conserver `python3 main.py` et des imports simples. Les données, documents,
tests et outils ont chacun leur répertoire. Aucun chemin absolu propre à une machine
n'est nécessaire à l'exécution.

## UML synchronisé

```bash
python3 tools/uml_live.py
```

Ouvrir **http://127.0.0.1:8765** et garder le serveur actif. Le diagramme est
extrait du code Python par AST ; la page détecte les changements chaque seconde.
Elle affiche uniquement les classes, leurs relations et une légende UML discrète :
`1` = exactement un objet, `0..*` = zéro à plusieurs, flèche ouverte = association
navigable, `+` = public, `#` = protégé. Les multiplicités sont indiquées côté cible.

代码保存后自动更新。语法错误期间保留上一张有效图，浏览器标签标题提示同步暂停。
双击 `docs/uml/uml.html` 查看静态导出；实时同步需访问上述本地网址。

```bash
python3 tools/uml_live.py --export     # Régénérer HTML et SVG
python3 tools/uml_live.py --port 8767  # Autre port
```

## Choix de conception

- `Plante` normalise et valide ses six champs, fournit `__str__` et `vers_dict`.
- `Herbier` indexe les plantes par nom scientifique normalisé. Les copies à l'entrée
  et à la sortie protègent l'index des mutations extérieures.
- La recherche partielle et les filtres sont insensibles à la casse et aux espaces.
- `nettoyer_plante` ne modifie pas les données originales ; `valider_plante` retourne
  une liste d'erreurs ; `detecter_doublons` regroupe les positions par clé scientifique.
- Espaces réduits, cycles en minuscules, famille latine (`Solanacées` → `Solanaceae`).
  Besoins sans accents, séparateur `_`, sauf `mi-ombre`. `arrosage_regulier` reste
  distinct d'`arrosage_moyen` ; `ombre` reste distinct de `mi-ombre`.
- Nom, nom scientifique et famille obligatoires ; cycle contrôlé ; besoins en liste
  de valeurs reconnues (liste vide acceptée). Photo `null` ou absente acceptée.
- Première entrée valide conservée en cas de doublon. Entrée 11 rejetée pour nom vide,
  Basilic 16 conservé ; Tomate 2 et Carotte 14 ignorées. Bilan : **16 → 13 plantes**.
  Les 25 plantes / 12 familles de l'écran illustratif du sujet ne sont pas le jeu fourni.
- JSON mal formé, structure incorrecte ou fichier entièrement invalide : collection
  courante préservée. Fichier partiellement valide : import des entrées valides avec
  rapport. `[]` vide explicitement la collection.
- Quiz : plantes sans répétition (`random.sample`), trois distracteurs distincts,
  choix mélangés (`random.shuffle`). En révision, les distracteurs viennent de toutes
  les familles. Moins de cinq plantes : nombre adapté ; moins de quatre familles :
  message explicite. Une saisie autre que A–D est redemandée.

## Tests et documentation

```bash
python3 -m unittest discover -v
python3 plante.py
```

Les tests vérifient les exigences du sujet, les cas limites, le score, les fichiers
invalides, l'intégrité de l'index et la régénération UML. GitHub Actions exécutera
les tests sur Python 3.9, 3.12 et 3.13 et vérifiera la génération du diagramme.

- [Rapport français, trois pages A4](docs/rapport.html)
- [Bilan de nettoyage](docs/rapport_nettoyage.json)
- [Résultats des tests](docs/resultats_tests.txt)
- [Diagramme UML vectoriel](docs/uml/uml.svg)

## Préparation GitHub

Le dossier courant est la racine prévue du dépôt. Les caches Python, environnements
virtuels, fichiers système et données personnelles `data/local/` sont ignorés.
Les exports UML sont versionnés pour être consultables sans lancer Python ; les
régénérer après une modification des classes. Aucune dépendance externe ni secret
n'est nécessaire. Le workflow CI s'activera lors du premier envoi sur GitHub.
