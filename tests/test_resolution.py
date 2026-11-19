"""Tests tirés des exemples et de la table de Résolution du livre (p. 28 à 35).

Les cases vérifiées ici ont été relevées une à une sur la table imprimée :
(caractéristique, ajustement) -> (chances, particulière, échec total).
"""

import pytest

from reve import Resultat, ajustement_final, chances, jet, qualifier, qualite_oeuvre, seuils

CASES_TABLE = [
    ((1, -10), (1, 1, 92)),
    ((4, -10), (1, 1, 92)),
    ((10, -10), (2, 1, 92)),
    ((4, -9), (2, 1, 92)),
    ((6, -6), (12, 3, 93)),
    ((5, -4), (15, 3, 93)),
    ((15, -5), (37, 8, 95)),
    ((9, -2), (36, 8, 95)),
    ((19, -3), (66, 14, 98)),
    ((9, 0), (45, 9, 96)),
    ((21, -7), (31, 7, 95)),
    ((10, 2), (60, 12, 97)),
    ((11, 2), (66, 14, 98)),
    ((3, 7), (25, 5, 94)),
    ((17, 1), (93, 19, 100)),
    ((20, 0), (100, 20, 100)),
    ((16, 3), (104, 21, None)),
    ((13, 7), (110, 22, None)),
    ((21, 7), (178, 36, None)),
]


@pytest.mark.parametrize(("entree", "attendu"), CASES_TABLE)
def test_cases_de_la_table(entree, attendu):
    s = seuils(*entree)
    assert (s.chances, s.particuliere, s.echec_total) == attendu


def test_extrapolation_hors_table():
    # 22 à +12 : caractéristique x11, soit 242 % (significative 121, particulière 49).
    s = seuils(22, 12)
    assert (s.chances, s.significative, s.particuliere) == (242, 121, 49)


def test_nitouche_haie_30_pourcent():
    s = seuils(10, -4)  # 10 x 3 = 30 %
    assert s.chances == 30
    assert qualifier(6, s) is Resultat.PARTICULIERE
    assert qualifier(7, s) is Resultat.SIGNIFICATIVE
    assert qualifier(15, s) is Resultat.SIGNIFICATIVE
    assert qualifier(16, s) is Resultat.NORMALE
    assert qualifier(30, s) is Resultat.NORMALE
    assert qualifier(31, s) is Resultat.ECHEC
    assert qualifier(85, s) is Resultat.ECHEC
    assert qualifier(86, s) is Resultat.ECHEC_PARTICULIER
    assert qualifier(93, s) is Resultat.ECHEC_PARTICULIER
    assert qualifier(94, s) is Resultat.ECHEC_TOTAL


def test_nitouche_discretion_78_pourcent():
    s = seuils(13, 2)  # 13 x 6 = 78 %
    assert s.chances == 78
    assert (s.significative, s.particuliere, s.echec_particulier, s.echec_total) == (39, 16, 96, 99)


def test_nitouche_fatiguee_a_moins_7():
    a = ajustement_final(difficulte=-2, competences=[-2], etat_general=-3)
    assert a == -7
    assert chances(10, a) == 15


def test_competences_concurrentes_prend_la_plus_basse():
    assert ajustement_final(0, [3, -3]) == -3


def test_hors_table_negatif():
    s = seuils(15, -11)
    assert s.chances == 1
    assert qualifier(1, s) is Resultat.NORMALE
    assert qualifier(50, s) is Resultat.ECHEC_PARTICULIER
    assert qualifier(90, s) is Resultat.ECHEC_TOTAL
    s = seuils(15, -17)
    assert qualifier(1, s) is Resultat.ECHEC_TOTAL


def test_00_au_dessus_de_100_est_un_echec_normal():
    s = seuils(21, 7)
    assert qualifier(100, s) is Resultat.ECHEC
    assert qualifier(89, s) is Resultat.SIGNIFICATIVE
    assert qualifier(99, s) is Resultat.NORMALE


def test_ragout_de_nitouche():
    # ODOGOÛT 7, Cuisine -4, difficulté -1 : 17 %, tirage 86, échec particulier, qualité -8.
    j = jet(7, difficulte=-1, competences=[-4], tirage=86)
    assert j.seuils.chances == 17
    assert j.resultat is Resultat.ECHEC_PARTICULIER
    assert qualite_oeuvre(-4, j.resultat) == -8


def test_ragout_de_brucelin():
    # ODOGOÛT 13, Cuisine +3, difficulté -1 : 78 %, tirage 25, significative, qualité +4.
    j = jet(13, difficulte=-1, competences=[3], tirage=25)
    assert j.seuils.chances == 78
    assert j.resultat is Resultat.SIGNIFICATIVE
    assert qualite_oeuvre(3, j.resultat) == 4


def test_particuliere_garantit_qualite_zero():
    assert qualite_oeuvre(-5, Resultat.PARTICULIERE) == 0


def test_explication_lisible():
    texte = jet(10, difficulte=-2, competences=[-2], tirage=12).explication()
    assert "30 %" in texte
    assert "réussite significative" in texte
