"""UML hors ligne généré par AST ; serveur local et actualisation automatique."""

import argparse
import ast
import hashlib
import html
import json
import textwrap
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SORTIE = RACINE / "docs" / "uml"


def sources():
    return sorted(p for p in RACINE.glob("*.py")
                  if not p.name.startswith("test_") and p.name != "uml_live.py")


def modele():
    """Extraire classes, attributs annotés, signatures et dépendances réelles."""
    classes = []
    for fichier in sources():
        arbre = ast.parse(fichier.read_text(encoding="utf-8"), filename=fichier.name)
        for classe in (n for n in arbre.body if isinstance(n, ast.ClassDef)):
            attributs, methodes, references = {}, [], set()
            for noeud in ast.walk(classe):
                if isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Attribute):
                    if isinstance(noeud.target.value, ast.Name) and noeud.target.value.id == "self":
                        attributs[noeud.target.attr] = ast.unparse(noeud.annotation)
                if isinstance(noeud, ast.Name):
                    references.add(noeud.id)
            for methode in classe.body:
                if isinstance(methode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    arguments = ast.unparse(methode.args)
                    arguments = arguments.removeprefix("self, ") if arguments != "self" else ""
                    retour = " → " + ast.unparse(methode.returns) if methode.returns else ""
                    methodes.append(f"{methode.name}({arguments}){retour}")
            classes.append(dict(nom=classe.name, fichier=fichier.name, attributs=attributs,
                                methodes=methodes, references=references,
                                bases=[ast.unparse(b) for b in classe.bases]))
    relations = []
    noms = {c["nom"] for c in classes}
    for classe in classes:
        for cible in sorted((classe["references"] & noms) - {classe["nom"]}):
            attributs = [t for t in classe["attributs"].values()
                         if cible in {n.id for n in ast.walk(ast.parse(t, mode="eval")) if isinstance(n, ast.Name)}]
            nature = ("héritage" if cible in classe["bases"] else
                      "association 0..*" if any(t.startswith(("list[", "dict[")) for t in attributs) else
                      "association 1" if attributs else "dépendance")
            relations.append((classe["nom"], cible, nature))
    return classes, relations


def generer_svg():
    classes, relations = modele()
    # Cycle de dépendances disposé en carré : aucun croisement des quatre liens.
    ordre = {"Herbier": 0, "Plante": 1, "Quiz": 2, "Question": 3}
    classes.sort(key=lambda c: (ordre.get(c["nom"], 4), c["nom"]))
    largeur, intervalle, marge = 570, 150, 40
    positions, blocs = {}, {}
    for classe in classes:
        attributs = [("# " if n.startswith("_") else "+ ") + n + ": " + t
                     for n, t in classe["attributs"].items()]
        methodes = ["+ " + m.replace(" → ", " : ") for m in classe["methodes"]]
        sections = [[ligne for membre in section for ligne in
                     textwrap.wrap(membre, width=66, subsequent_indent="    ",
                                   break_long_words=False, break_on_hyphens=False)]
                    for section in (attributs, methodes)]
        blocs[classe["nom"]] = sections
    y = marge
    for debut in range(0, len(classes), 2):
        hauteurs = []
        for colonne, classe in enumerate(classes[debut:debut + 2]):
            attributs, methodes = blocs[classe["nom"]]
            hauteur = 44 + max(1, len(attributs)) * 23 + 22 + max(1, len(methodes)) * 23 + 22
            positions[classe["nom"]] = (marge + colonne * (largeur + intervalle), y, hauteur)
            hauteurs.append(hauteur)
        y += max(hauteurs) + 120
    total = marge * 2 + largeur * 2 + intervalle
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagramme de classes" width="{total}" height="{y+80}" viewBox="0 0 {total} {y+80}">',
           '<defs><marker id="fleche" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11" fill="none" stroke="#222" stroke-width="1.2"/></marker><marker id="heritage" markerWidth="14" markerHeight="14" refX="13" refY="7" orient="auto"><path d="M1,1 L13,7 L1,13 Z" fill="white" stroke="#222"/></marker></defs>',
           '<rect width="100%" height="100%" fill="white"/>',
           '<g fill="#161616" font-family="Menlo,Consolas,monospace" font-size="13">']
    for origine, cible, nature in relations:
        ox, oy, oh = positions[origine]
        tx, ty, th = positions[cible]
        if oy == ty:
            droite = ox < tx
            sx, ex = (ox + largeur, tx) if droite else (ox, tx + largeur)
            sy = ey = oy + 75
            chemin = f'M{sx} {sy} H{ex}'
            lx, ly = (ex - 14 if droite else ex + 14), ey - 12
            ancre = "end" if droite else "start"
        else:
            descend = oy < ty
            sx, ex = ox + largeur / 2, tx + largeur / 2
            sy, ey = (oy + oh, ty) if descend else (oy, ty + th)
            milieu = (sy + ey) / 2
            chemin = f'M{sx} {sy} V{milieu} H{ex} V{ey}'
            lx, ly, ancre = ex + 12, (ey - 12 if descend else ey + 22), "start"
        marqueur = "heritage" if nature == "héritage" else "fleche"
        svg.append(f'<path d="{chemin}" fill="none" stroke="#222" stroke-width="1.3" marker-end="url(#{marqueur})" stroke-dasharray="{"6 4" if nature == "dépendance" else "none"}"/>')
        if nature.startswith("association"):
            svg.append(f'<text x="{lx}" y="{ly}" text-anchor="{ancre}" font-family="Arial,sans-serif" font-size="15">{nature.split()[-1]}</text>')
    for classe in classes:
        x, haut, hauteur = positions[classe["nom"]]
        attributs, methodes = blocs[classe["nom"]]
        svg.append(f'<rect x="{x}" y="{haut}" width="{largeur}" height="{hauteur}" fill="white" stroke="#222" stroke-width="1.3"/>')
        svg.append(f'<text x="{x+largeur/2}" y="{haut+28}" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" font-weight="bold">{html.escape(classe["nom"])}</text>')
        ligne = haut + 44
        for section in (attributs, methodes):
            svg.append(f'<path d="M{x} {ligne} H{x+largeur}" stroke="#222" stroke-width="1"/>')
            ligne += 9
            for texte in section or [""]:
                ligne += 23
                svg.append(f'<text x="{x+16}" y="{ligne}" xml:space="preserve">{html.escape(texte)}</text>')
            ligne += 13
    svg.append(f'<path d="M40 {y-40} H{total-40}" stroke="#aaa"/>')
    legende = [
        "LÉGENDE   1 : exactement un objet   ·   0..* : zéro à plusieurs objets",
        "Trait plein + flèche ouverte : association navigable vers la classe cible ; nombre côté cible = multiplicité.",
        "+ : public   ·   # : protégé   ·   Chaque classe : nom / attributs / opérations.",
    ]
    for index, texte in enumerate(legende):
        svg.append(f'<text x="40" y="{y-12+index*28}" font-family="Arial,sans-serif" font-size="15">{html.escape(texte)}</text>')
    svg.append('</g></svg>')
    return "".join(svg), relations


def version():
    return hashlib.sha256(b"".join(p.name.encode() + p.read_bytes() for p in sources())).hexdigest()


def actualiser():
    svg, relations = generer_svg()
    SORTIE.mkdir(parents=True, exist_ok=True)
    SORTIE.joinpath("uml.svg").write_text(svg, encoding="utf-8")
    page = '''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Herbier · UML vivant</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>html,body{margin:0;background:#fff}#diagramme{max-width:1440px;margin:auto}svg{display:block;width:100%;height:auto}@media print{@page{size:A3 landscape;margin:8mm}#diagramme{max-width:none}svg{max-height:95vh}}</style>
<main id="diagramme">''' + svg + '''</main>
<script>
let derniere = null;
async function actualiser(){
 if(location.protocol === 'file:') return;
 try {
  const r = await fetch('/api/uml', {cache:'no-store'}); const d = await r.json();
  if(!r.ok) throw new Error(d.erreur);
  if(derniere !== null && derniere !== d.version) { location.reload(); return; }
  derniere = d.version;
   document.title = 'Herbier · UML';
 } catch(e) {document.title = 'Herbier · UML — synchronisation suspendue';}
}
actualiser(); setInterval(actualiser, 1000);
</script></html>'''
    SORTIE.joinpath("uml.html").write_text(page, encoding="utf-8")


class Gestionnaire(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Recalcul à chaque requête : aucune classe métier n'est importée/exécutée.
            actualiser()
            if self.path == "/api/uml":
                contenu = json.dumps({"version": version()}).encode()
                mime = "application/json"
            elif self.path in ("/", "/uml.html", "/uml.svg"):
                fichier = "uml.svg" if self.path.endswith(".svg") else "uml.html"
                contenu = SORTIE.joinpath(fichier).read_bytes()
                mime = "image/svg+xml" if fichier.endswith("svg") else "text/html"
            else:
                self.send_error(404)
                return
            self.send_response(200)
        except (SyntaxError, OSError, ValueError) as erreur:
            contenu = json.dumps({"erreur": str(erreur)}).encode()
            mime = "application/json"
            self.send_response(422)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(contenu)))
        self.end_headers()
        self.wfile.write(contenu)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", action="store_true", help="Générer HTML/SVG puis quitter")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    actualiser()
    if not args.export:
        serveur = ThreadingHTTPServer(("127.0.0.1", args.port), Gestionnaire)
        print(f"UML synchronisé : http://127.0.0.1:{args.port} (Ctrl+C pour arrêter)", flush=True)
        try:
            serveur.serve_forever()
        except KeyboardInterrupt:
            serveur.server_close()
