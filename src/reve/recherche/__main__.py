"""Ligne de commande de la recherche.

    python -m reve.recherche indexer livres/Rdd.pdf --decalage 2
    python -m reve.recherche chercher "comment lancer un sort d'Hypnos"
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

from . import ollama
from .extraction import extraire
from .index import Index, decouper

DOSSIER_INDEX = Path("index")


def indexer(args) -> None:
    pages = extraire(args.pdf, args.decalage)
    source = args.source or Path(args.pdf).stem
    passages = decouper(pages, source)
    vecteurs = None
    if args.sens:
        if not ollama.disponible():
            sys.exit("Ollama ne répond pas sur localhost:11434. Lancez-le ou retirez --sens.")
        print(f"Calcul des plongements de {len(passages)} passages avec {args.modele}…")
        vecteurs = ollama.plongeur(args.modele)([p.texte for p in passages])
    Index(passages, vecteurs).enregistrer(args.index)
    print(f"{len(pages)} pages, {len(passages)} passages indexés dans {args.index}/")


def chercher(args) -> None:
    plongeur = ollama.plongeur(args.modele) if ollama.disponible() else None
    index = Index.charger(args.index, plongeur)
    for r in index.chercher(args.question, args.n):
        print(f"\n[{r.rang}] {r.passage.reference()}")
        print(textwrap.fill(r.passage.texte[: args.longueur], 100, initial_indent="    ", subsequent_indent="    "))


def evaluer(args) -> None:
    import json

    plongeur = ollama.plongeur(args.modele) if ollama.disponible() else None
    index = Index.charger(args.index, plongeur)
    jeu = json.loads(Path(args.questions).read_text(encoding="utf-8"))["questions"]
    trouves, rr = 0, 0.0
    for q in jeu:
        rangs = [r.rang for r in index.chercher(q["question"], args.n) if r.passage.page_livre in q["pages"]]
        if rangs:
            trouves += 1
            rr += 1 / rangs[0]
        print(f"{'OK ' if rangs else '-- '} {q['question']}  (rang {rangs[0] if rangs else '-'})")
    mode = "mots-clés + sens" if index.vecteurs is not None and plongeur else "mots-clés"
    print(f"\nRecherche par {mode} : bonne page dans les {args.n} premiers pour {trouves}/{len(jeu)} questions, "
          f"rang réciproque moyen {rr / len(jeu):.2f}")


def main() -> None:
    p = argparse.ArgumentParser(prog="reve.recherche")
    p.add_argument("--index", type=Path, default=DOSSIER_INDEX, help="dossier de l'index (local)")
    p.add_argument("--modele", default=ollama.MODELE, help="modèle de plongement Ollama")
    sous = p.add_subparsers(required=True)

    i = sous.add_parser("indexer", help="extraire un PDF et construire l'index")
    i.add_argument("pdf")
    i.add_argument("--decalage", type=int, default=0, help="page PDF moins page imprimée (2 pour Rdd.pdf)")
    i.add_argument("--source", help="nom court de la source dans les références")
    i.add_argument("--sens", action="store_true", help="ajouter la recherche par le sens (Ollama)")
    i.set_defaults(action=indexer)

    c = sous.add_parser("chercher", help="chercher des passages")
    c.add_argument("question")
    c.add_argument("-n", type=int, default=5)
    c.add_argument("--longueur", type=int, default=600, help="caractères affichés par passage")
    c.set_defaults(action=chercher)

    e = sous.add_parser("evaluer", help="mesurer la qualité sur une liste de questions")
    e.add_argument("questions", nargs="?", default="evaluation/questions_rdd.json")
    e.add_argument("-n", type=int, default=5)
    e.set_defaults(action=evaluer)

    args = p.parse_args()
    args.action(args)


if __name__ == "__main__":
    main()
