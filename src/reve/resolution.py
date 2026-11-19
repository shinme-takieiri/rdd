"""Table de Résolution et résultats spéciaux (règles de base, p. 28 à 35 du livre).

Tout est calculé à partir des règles de construction de la table, sans
recopier la table elle-même :

* chances de succès = caractéristique × multiplicateur de la colonne,
  arrondi à l'inférieur, avec un minimum de 1 ;
* multiplicateur : -10 -> 1/4, -9 -> 1/2, puis à partir de -8 :
  (ajustement + 10) / 2, soit ×1 à -8, ×5 à 0, ×10 à +10 ;
* au-delà de -10, une échelle à part (voir ``_ECHEC_TOTAL_HORS_TABLE``).

Les seuils des résultats spéciaux suivent le principe du livre :
particulière ≈ 20 % des chances, significative = 50 %, échec particulier
≈ 20 % des chances d'échec, échec total ≈ 10 %. Ils sont calculés par
tranches de 5 % comme la table des résultats spéciaux.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from math import ceil

AJUSTEMENT_MIN_TABLE = -10
AJUSTEMENT_TOUT_ECHEC_TOTAL = -17

# Au-delà de -10 : chances fixées à 01, plus de significative ni de
# particulière, tout échec est particulier, et l'échec total commence
# à ce seuil.
_ECHEC_TOTAL_HORS_TABLE = {-11: 90, -12: 70, -13: 50, -14: 30, -15: 10, -16: 2}

DIFFICULTES = {
    -10: "chimérique",
    -9: "presque insurmontable",
    -8: "extrêmement difficile",
    -7: "très difficile",
    -6: "difficile",
    -5: "problématique",
    -4: "laborieux",
    -3: "très malaisé",
    -2: "malaisé",
    -1: "assez malaisé",
    0: "moyen",
    1: "assez facile",
    2: "facile",
    3: "très facile",
    4: "encore plus facile",
}


class Resultat(Enum):
    """Les six qualités de résultat, de la meilleure à la pire."""

    PARTICULIERE = "réussite particulière"
    SIGNIFICATIVE = "réussite significative"
    NORMALE = "réussite normale"
    ECHEC = "échec normal"
    ECHEC_PARTICULIER = "échec particulier"
    ECHEC_TOTAL = "échec total"

    @property
    def reussite(self) -> bool:
        return self in (Resultat.PARTICULIERE, Resultat.SIGNIFICATIVE, Resultat.NORMALE)


POINTS_DE_QUALITE = {
    Resultat.ECHEC_TOTAL: -6,
    Resultat.ECHEC_PARTICULIER: -4,
    Resultat.ECHEC: -2,
    Resultat.NORMALE: 0,
    Resultat.SIGNIFICATIVE: 1,
    Resultat.PARTICULIERE: 2,
}


def multiplicateur(ajustement: int) -> Fraction:
    """Multiplicateur de la caractéristique pour une colonne de la table."""
    if ajustement < AJUSTEMENT_MIN_TABLE:
        raise ValueError("au-delà de -10, utiliser seuils() qui gère l'échelle hors table")
    if ajustement == -10:
        return Fraction(1, 4)
    if ajustement == -9:
        return Fraction(1, 2)
    return Fraction(ajustement + 10, 2)


def chances(caracteristique: int, ajustement: int) -> int:
    """Chances de succès en % (peuvent dépasser 100)."""
    if caracteristique < 1:
        raise ValueError("une caractéristique vaut au moins 1")
    if ajustement < AJUSTEMENT_MIN_TABLE:
        return 1
    return max(1, int(caracteristique * multiplicateur(ajustement)))


@dataclass(frozen=True)
class Seuils:
    """Seuils d'un jet : un tirage ≤ seuil (réussites) ou ≥ seuil (échecs).

    ``None`` signifie que ce résultat est impossible.
    """

    chances: int
    particuliere: int | None
    significative: int | None
    echec_particulier: int | None
    echec_total: int | None


def seuils(caracteristique: int, ajustement: int) -> Seuils:
    if ajustement <= AJUSTEMENT_TOUT_ECHEC_TOTAL:
        return Seuils(1, None, None, None, 1)
    if ajustement < AJUSTEMENT_MIN_TABLE:
        return Seuils(1, None, None, 2, _ECHEC_TOTAL_HORS_TABLE[ajustement])
    c = chances(caracteristique, ajustement)
    tranche = ceil(c / 5)  # 01-05 -> 1, 06-10 -> 2, ...
    significative = c // 2 or None
    if c > 100:
        # Plus d'échec particulier ni total ; 00 reste un échec normal.
        return Seuils(c, tranche, significative, None, None)
    return Seuils(
        chances=c,
        particuliere=tranche,
        significative=significative,
        echec_particulier=80 + tranche,
        echec_total=min(100, 91 + ceil(tranche / 2)),
    )


def qualifier(tirage: int, s: Seuils) -> Resultat:
    """Qualité du résultat d'un tirage de 1 à 100 (00 = 100)."""
    if not 1 <= tirage <= 100:
        raise ValueError("un jet de pourcentage va de 01 à 00 (100)")
    if s.echec_total is not None and tirage >= s.echec_total:
        return Resultat.ECHEC_TOTAL
    if tirage == 100 and s.chances > 100:
        return Resultat.ECHEC
    if tirage <= s.chances:
        if s.particuliere is not None and tirage <= s.particuliere:
            return Resultat.PARTICULIERE
        if s.significative is not None and tirage <= s.significative:
            return Resultat.SIGNIFICATIVE
        return Resultat.NORMALE
    if s.echec_particulier is not None and tirage >= s.echec_particulier:
        return Resultat.ECHEC_PARTICULIER
    return Resultat.ECHEC
