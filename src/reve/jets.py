"""Jets de Caractéristique/Compétence, avec explication du calcul."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .resolution import POINTS_DE_QUALITE, Resultat, Seuils, qualifier, seuils


def ajustement_final(difficulte: int, competences: list[int] | None = None, etat_general: int = 0) -> int:
    """Somme de la difficulté, de la compétence et de l'état général.

    Si plusieurs compétences entrent en jeu, la plus basse s'applique.
    Sans compétence pertinente, seule la difficulté (et l'état) compte.
    """
    competence = min(competences) if competences else 0
    return difficulte + competence + etat_general


@dataclass
class Jet:
    caracteristique: int
    ajustement: int
    seuils: Seuils
    tirage: int
    resultat: Resultat
    detail: list[str] = field(default_factory=list)

    @property
    def points_de_qualite(self) -> int:
        return POINTS_DE_QUALITE[self.resultat]

    def explication(self) -> str:
        return "\n".join(self.detail)


def lancer_d100(rng: random.Random | None = None) -> int:
    return (rng or random).randint(1, 100)


def jet(
    caracteristique: int,
    difficulte: int = 0,
    competences: list[int] | None = None,
    etat_general: int = 0,
    tirage: int | None = None,
    rng: random.Random | None = None,
) -> Jet:
    """Résout un jet complet. ``tirage`` force le résultat du d100 (00 = 100)."""
    ajust = ajustement_final(difficulte, competences, etat_general)
    s = seuils(caracteristique, ajust)
    t = tirage if tirage is not None else lancer_d100(rng)
    r = qualifier(t, s)

    detail = []
    morceaux = [f"difficulté {difficulte:+d}"]
    if competences:
        retenue = min(competences)
        note = " (la plus basse)" if len(competences) > 1 else ""
        morceaux.append(f"compétence {retenue:+d}{note}")
    if etat_general:
        morceaux.append(f"état général {etat_general:+d}")
    detail.append(f"Ajustement final : {' + '.join(morceaux)} = {ajust:+d}")
    detail.append(f"Chances : {caracteristique} à {ajust:+d} = {s.chances} %")
    bornes = []
    if s.particuliere is not None:
        bornes.append(f"particulière ≤ {s.particuliere:02d}")
    if s.significative is not None:
        bornes.append(f"significative ≤ {s.significative:02d}")
    if s.echec_particulier is not None:
        bornes.append(f"échec particulier ≥ {s.echec_particulier % 100:02d}")
    if s.echec_total is not None:
        bornes.append(f"échec total ≥ {s.echec_total % 100:02d}")
    detail.append("Seuils : " + ", ".join(bornes))
    detail.append(f"Tirage : {t % 100:02d} -> {r.value}")
    return Jet(caracteristique, ajust, s, t, r, detail)


def qualite_oeuvre(niveau_competence: int, resultat: Resultat) -> int:
    """Qualité d'une œuvre (cuisine, musique...) : compétence + points obtenus.

    Une réussite particulière garantit une qualité d'au moins zéro.
    """
    q = niveau_competence + POINTS_DE_QUALITE[resultat]
    if resultat is Resultat.PARTICULIERE:
        q = max(0, q)
    return q
