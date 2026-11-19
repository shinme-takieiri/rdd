"""Extraction du texte d'un PDF mis en page sur deux colonnes.

Le livre de règles est composé en deux colonnes, avec des encadrés et des
titres sur toute la largeur. Une extraction naïve mélange les colonnes ;
ici on remet les blocs dans l'ordre de lecture :

1. les blocs larges (plus de 60 % de la zone de texte) coupent la page en
   bandes horizontales ;
2. dans chaque bande, on lit la colonne de gauche puis celle de droite.

Les titres du livre utilisent une police décorative dont l'encodage est
illisible : leur texte est écarté, mais leur position sert à découper la page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_CARACTERES_ILLISIBLES = re.compile(r"[\x00-\x08\x0b-\x1f�]")
_CESURE = re.compile(r"(\w)-\n(\w)")
_ESPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class Bloc:
    x0: float
    y0: float
    x1: float
    y1: float
    texte: str

    @property
    def largeur(self) -> float:
        return self.x1 - self.x0

    @property
    def centre_x(self) -> float:
        return (self.x0 + self.x1) / 2


@dataclass(frozen=True)
class Page:
    numero_pdf: int  # à partir de 1
    numero_livre: int | None  # numéro imprimé, si on connaît le décalage
    blocs: list[str]

    @property
    def texte(self) -> str:
        return "\n\n".join(self.blocs)


def nettoyer(texte: str) -> str:
    texte = _CESURE.sub(r"\1\2", texte)
    return _ESPACES.sub(" ", texte).strip()


def est_lisible(texte: str) -> bool:
    if not texte.strip():
        return False
    illisibles = len(_CARACTERES_ILLISIBLES.findall(texte))
    return illisibles / max(1, len(texte)) < 0.05


def ordre_de_lecture(blocs: list[Bloc]) -> list[Bloc]:
    """Remet des blocs dans l'ordre de lecture d'une page à deux colonnes."""
    if not blocs:
        return []
    gauche_page = min(b.x0 for b in blocs)
    droite_page = max(b.x1 for b in blocs)
    largeur_texte = droite_page - gauche_page
    milieu = (gauche_page + droite_page) / 2

    larges = sorted((b for b in blocs if b.largeur > 0.6 * largeur_texte), key=lambda b: b.y0)
    etroits = [b for b in blocs if b.largeur <= 0.6 * largeur_texte]

    resultat: list[Bloc] = []
    haut_bande = float("-inf")
    for separateur in [*larges, None]:
        bas_bande = separateur.y0 if separateur else float("inf")
        bande = [b for b in etroits if haut_bande <= b.y0 < bas_bande]
        resultat += sorted((b for b in bande if b.centre_x < milieu), key=lambda b: b.y0)
        resultat += sorted((b for b in bande if b.centre_x >= milieu), key=lambda b: b.y0)
        if separateur:
            resultat.append(separateur)
            haut_bande = separateur.y0
    return resultat


def _est_numero_de_page(bloc: Bloc, hauteur_page: float) -> bool:
    return bloc.y0 > 0.9 * hauteur_page and bloc.texte.strip().isdigit()


def extraire(chemin_pdf: str | Path, decalage_pages: int = 0) -> list[Page]:
    """Extrait les pages d'un PDF.

    ``decalage_pages`` : numéro de page PDF moins numéro imprimé
    (2 pour la réédition Scriptarium : la page 33 du PDF est la page 31).
    """
    import pymupdf  # dépendance optionnelle, chargée seulement ici

    pages = []
    with pymupdf.open(chemin_pdf) as doc:
        for index, page in enumerate(doc):
            hauteur = page.rect.height
            blocs = [
                Bloc(x0, y0, x1, y1, texte)
                for x0, y0, x1, y1, texte, _, type_bloc in page.get_text("blocks")
                if type_bloc == 0
            ]
            blocs = [b for b in blocs if not _est_numero_de_page(b, hauteur)]
            # Les titres illisibles restent dans le calcul de l'ordre : ils
            # séparent souvent deux sections sur toute la largeur.
            textes = [
                t for b in ordre_de_lecture(blocs)
                if est_lisible(b.texte) and (t := nettoyer(b.texte))
            ]
            numero_livre = index + 1 - decalage_pages
            pages.append(Page(index + 1, numero_livre if numero_livre >= 1 else None, textes))
    return pages
