"""Ligne de commande : python -m reve 10 --difficulte -2 --competence -2"""

import argparse

from .jets import jet


def main() -> None:
    p = argparse.ArgumentParser(prog="reve", description="Jet de Caractéristique/Compétence")
    p.add_argument("caracteristique", type=int)
    p.add_argument("-d", "--difficulte", type=int, default=0)
    p.add_argument("-c", "--competence", type=int, action="append",
                   help="niveau de compétence ; répéter pour des compétences concurrentes")
    p.add_argument("-e", "--etat", type=int, default=0, help="état général (malus)")
    p.add_argument("-t", "--tirage", type=int, help="forcer le d100 (100 pour 00)")
    a = p.parse_args()
    print(jet(a.caracteristique, a.difficulte, a.competence, a.etat, a.tirage).explication())


if __name__ == "__main__":
    main()
