"""Tests du cahier des charges, des erreurs et des invariants du quiz."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from donnees import detecter_doublons, nettoyer_plante, valider_plante
from herbier import Herbier
from plante import Plante
from quiz import Quiz
from tools import uml_live

RACINE = Path(__file__).resolve().parents[1]


class TestsHerbier(unittest.TestCase):
    def setUp(self):
        self.herbier = Herbier()
        self.rapport = self.herbier.charger_json(RACINE / "data" / "plantes_degradees.json")

    def test_bilan_nettoyage(self):
        self.assertEqual(self.rapport["lus"], 16)
        self.assertEqual(self.rapport["acceptes"], 13)
        self.assertEqual(self.rapport["ignores"], [2, 14])
        self.assertEqual(self.rapport["erreurs"][0]["ligne"], 11)
        self.assertEqual(self.rapport["photos_absentes"], [7])

    def test_recherches(self):
        for requete in ("tom", "TOMATE", " tomate   "):
            self.assertEqual([p.nom for p in self.herbier.rechercher(requete)], ["Tomate"])
        self.assertEqual(self.herbier.rechercher("inexistante"), [])
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            self.herbier.afficher([])
        self.assertIn("Aucune plante", sortie.getvalue())

    def test_filtres(self):
        self.assertEqual([p.nom for p in self.herbier.filtrer_par_famille(" FABACEAE ")], ["Haricot", "Pois"])
        self.assertEqual(len(self.herbier.filtrer_par_cycle("VIVACE")), 7)
        self.assertEqual(len(self.herbier.filtrer_par_besoin("soleil")), 11)
        self.assertEqual([p.nom for p in self.herbier.filtrer(cycle="vivace", besoin="mi-ombre")], ["Menthe", "Ortie"])
        self.assertEqual(self.herbier.filtrer(cycle="vivace", besoin="ombre"), [])
        self.assertEqual(len(self.herbier.filtrer_par_famille("Solanacées")), 1)

    def test_normalisation(self):
        brute = dict(nom=" tomate ", nom_scientifique="Solanum   lycopersicum",
                     famille="Solanacées", cycle="Annuel", besoins=["arrosage régulier", "arrosage regulier"], photo=None)
        propre = nettoyer_plante(brute)
        self.assertEqual(propre["besoins"], ["arrosage_regulier"])
        self.assertEqual(propre["famille"], "Solanaceae")
        self.assertEqual(propre["nom_scientifique"], "Solanum lycopersicum")
        self.assertEqual(nettoyer_plante(propre), propre)
        self.assertEqual(brute["nom"], " tomate ")

    def test_validation(self):
        base = self.herbier.plantes[0].vers_dict()
        for champ, valeur in (("nom", ""), ("nom_scientifique", None), ("famille", 12),
                              ("cycle", []), ("besoins", "soleil"), ("besoins", [{}]), ("photo", 3)):
            with self.subTest(champ=champ, valeur=valeur):
                invalide = dict(base, **{champ: valeur})
                self.assertTrue(valider_plante(invalide))
                with self.assertRaises(ValueError):
                    nettoyer_plante(invalide)
        for valeur in (None, [], 5):
            with self.assertRaises(ValueError):
                nettoyer_plante(valeur)

    def test_photo_absente(self):
        menthe = self.herbier.rechercher("menthe")[0]
        self.assertIsNone(menthe.photo)
        self.assertIn("Photo : absente", str(menthe))

    def test_doublons(self):
        brut = json.loads((RACINE / "data" / "plantes_degradees.json").read_text())
        groupes = detecter_doublons(brut)
        self.assertEqual(groupes["daucus carota"], [13, 14])
        self.assertEqual(groupes["ocimum basilicum"], [11, 16])
        with self.assertRaises(ValueError):
            self.herbier.ajouter_plante(self.herbier.plantes[0])

    def test_ajout_suppression_index(self):
        plante = Plante("Test", "Test species", "Fabaceae", "vivace", ["ombre"], None)
        self.herbier.ajouter_plante(plante)
        plante.nom_scientifique = "Mutation extérieure"
        copie = self.herbier.rechercher_scientifique(" TEST  SPECIES ")
        self.assertEqual(copie.nom, "Test")
        copie.nom = "Autre"
        self.assertEqual(self.herbier.rechercher_scientifique("Test species").nom, "Test")
        self.herbier.supprimer_plante("test species")
        self.assertIsNone(self.herbier.rechercher_scientifique("test species"))
        with self.assertRaisesRegex(ValueError, "inconnue"):
            self.herbier.supprimer_plante("inconnue")

    def test_serialisation(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "herbier.json"
            self.herbier.sauvegarder_json(fichier)
            autre = Herbier()
            autre.charger_json(fichier)
            self.assertEqual([p.vers_dict() for p in autre.plantes], [p.vers_dict() for p in self.herbier.plantes])

    def test_fichiers_invalides_collection_conservee(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "test.json"
            with self.assertRaises(FileNotFoundError):
                self.herbier.charger_json(fichier)
            for contenu, exception in (("{", json.JSONDecodeError), ("{}", ValueError), ('[{"nom": ""}]', ValueError)):
                fichier.write_text(contenu)
                with self.assertRaises(exception):
                    self.herbier.charger_json(fichier)
                self.assertEqual(len(self.herbier.plantes), 13)
            fichier.write_text("[]")
            self.herbier.charger_json(fichier)
            self.assertEqual(self.herbier.plantes, [])

    def test_quiz_score_et_unicite(self):
        quiz = Quiz(self.herbier)
        questions = quiz.preparer()
        self.assertEqual(len({q.plante.nom_scientifique for q in questions}), 5)
        for i, question in enumerate(questions):
            self.assertEqual(len(set(question.choix)), 4)
            index = question.choix.index(question.plante.famille)
            if i == 4:
                index = (index + 1) % 4
            quiz.repondre(str(index + 1))
        self.assertEqual(quiz.resultat(), dict(score=4, total=5, pourcentage=80, appreciation="Très bien !"))
        with self.assertRaises(ValueError):
            quiz.repondre("1")

    def test_revision_et_saisie_quiz(self):
        quiz = Quiz(self.herbier)
        questions = quiz.preparer(famille="Lamiaceae")
        self.assertEqual(len(questions), 4)
        self.assertTrue(all(q.plante.famille == "Lamiaceae" for q in questions))
        for invalide in ("abc", "A", "0", "5", "", "1.0"):
            with self.assertRaises(ValueError):
                quiz.repondre(invalide)
        self.assertEqual(quiz.reponses, [])
        for q in questions:
            quiz.repondre(f" {q.choix.index(q.plante.famille) + 1} ")
        self.assertEqual(quiz.resultat()["pourcentage"], 100)

    def test_quiz_familles_insuffisantes(self):
        with self.assertRaises(ValueError):
            Quiz(Herbier()).preparer()
        petit = Herbier()
        for p in self.herbier.filtrer_par_famille("Fabaceae"):
            petit.ajouter_plante(p)
        with self.assertRaisesRegex(ValueError, "quatre familles"):
            Quiz(petit).preparer()

    def test_menu_saisie_incorrecte(self):
        execution = subprocess.run([sys.executable, str(RACINE / "main.py")],
                                   input="abc\n99\n2\ninexistante\n0\n", text=True, capture_output=True)
        self.assertEqual(execution.returncode, 0)
        self.assertIn("Saisie ou données incorrectes", execution.stdout)
        self.assertIn("Aucune plante trouvée", execution.stdout)
        self.assertIn("Au revoir", execution.stdout)

    def test_uml_synchronise_avec_sources(self):
        with tempfile.TemporaryDirectory() as dossier:
            fichier = Path(dossier) / "exemple.py"
            fichier.write_text("class Plante:\n    def nom(self): pass\n")
            with patch.object(uml_live, "RACINE", Path(dossier)), patch.object(uml_live, "SORTIE", Path(dossier)):
                uml_live.actualiser()
                ancienne = uml_live.version()
                fichier.write_text("class Plante:\n    def nouvelle_methode(self): pass\n")
                uml_live.actualiser()
                self.assertNotEqual(ancienne, uml_live.version())
                self.assertIn("nouvelle_methode", (Path(dossier) / "uml.svg").read_text())
                fichier.write_text("class Plante:")
                with self.assertRaises(SyntaxError):
                    uml_live.actualiser()
                self.assertIn("nouvelle_methode", (Path(dossier) / "uml.svg").read_text())


if __name__ == "__main__":
    unittest.main()
