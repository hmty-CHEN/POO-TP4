"""Nettoyage, validation et détection des doublons, sans modifier les sources."""

import unicodedata

CYCLES = {"annuel", "bisannuel", "vivace"}
BESOINS = {"soleil", "mi-ombre", "ombre", "arrosage_faible",
           "arrosage_moyen", "arrosage_frequent", "arrosage_regulier"}
CHAMPS = ("nom", "nom_scientifique", "famille", "cycle", "besoins", "photo")


def texte(valeur):
    """Réduire les espaces ; refuser de convertir silencieusement un nombre."""
    return " ".join(valeur.split()) if isinstance(valeur, str) else valeur


def cle(valeur):
    """Clé de comparaison insensible à la casse, aux accents et aux espaces."""
    if not isinstance(valeur, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", texte(valeur).casefold())
                   if not unicodedata.combining(c))


def normaliser_famille(valeur):
    if not isinstance(valeur, str):
        return valeur
    return {"solanacees": "Solanaceae"}.get(cle(valeur), texte(valeur).capitalize())


def normaliser_besoin(valeur):
    if not isinstance(valeur, str):
        return valeur
    return cle(valeur).replace("-", "_").replace(" ", "_").replace("mi_ombre", "mi-ombre")


def valider_plante(plante):
    """Retourner un rapport d'erreurs (liste vide si les données sont valides)."""
    if hasattr(plante, "vers_dict"):
        plante = plante.vers_dict()
    if not isinstance(plante, dict):
        return ["Une plante doit être un objet JSON."]
    erreurs = []
    for champ in ("nom", "nom_scientifique", "famille"):
        if not isinstance(plante.get(champ), str) or not plante[champ].strip():
            erreurs.append(f"{champ} : texte obligatoire manquant ou incorrect")
    cycle = plante.get("cycle")
    if not isinstance(cycle, str) or cycle not in CYCLES:
        erreurs.append("cycle : choisir annuel, bisannuel ou vivace")
    besoins = plante.get("besoins")
    if not isinstance(besoins, list):
        erreurs.append("besoins : une liste est obligatoire")
    elif any(not isinstance(b, str) or b not in BESOINS for b in besoins):
        erreurs.append("besoins : valeur inconnue")
    if plante.get("photo") is not None and not isinstance(plante["photo"], str):
        erreurs.append("photo : texte ou null attendu")
    return erreurs


def nettoyer_plante(donnees):
    """Retourner les six champs normalisés ; signaler l'invalide par ValueError."""
    if not isinstance(donnees, dict):
        raise ValueError("Une plante doit être un objet JSON.")
    resultat = {champ: texte(donnees.get(champ)) for champ in CHAMPS}
    if isinstance(resultat["nom"], str):
        resultat["nom"] = resultat["nom"].capitalize()
    resultat["famille"] = normaliser_famille(resultat["famille"])
    if isinstance(resultat["cycle"], str):
        resultat["cycle"] = cle(resultat["cycle"])
    if isinstance(resultat["besoins"], list):
        resultat["besoins"] = [normaliser_besoin(b) for b in resultat["besoins"]]
    erreurs = valider_plante(resultat)
    if erreurs:
        raise ValueError(" ; ".join(erreurs))
    resultat["besoins"] = list(dict.fromkeys(resultat["besoins"]))
    return resultat


def detecter_doublons(plantes):
    """Renvoyer les groupes de positions (base 1) de même nom scientifique."""
    groupes = {}
    for position, plante in enumerate(plantes, 1):
        donnees = plante.vers_dict() if hasattr(plante, "vers_dict") else plante
        if isinstance(donnees, dict):
            nom = cle(donnees.get("nom_scientifique"))
            if nom:
                groupes.setdefault(nom, []).append(position)
    return {nom: positions for nom, positions in groupes.items() if len(positions) > 1}
