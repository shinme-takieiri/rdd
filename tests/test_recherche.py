"""Tests de la recherche, sur des textes inventés (aucun texte du livre)."""

import pytest

from reve.recherche.extraction import Bloc, Page, est_lisible, extraire, nettoyer, ordre_de_lecture
from reve.recherche.index import Index, Passage, decouper, fusion_rrf, mots


def test_ordre_de_lecture_deux_colonnes_et_bandeau():
    blocs = [
        Bloc(330, 300, 520, 400, "droite bas"),
        Bloc(120, 100, 520, 140, "titre large"),
        Bloc(120, 160, 310, 280, "gauche haut"),
        Bloc(330, 160, 520, 280, "droite haut"),
        Bloc(120, 300, 310, 400, "gauche bas"),
        Bloc(120, 420, 520, 450, "bandeau"),
        Bloc(120, 470, 310, 500, "après le bandeau"),
    ]
    assert [b.texte for b in ordre_de_lecture(blocs)] == [
        "titre large", "gauche haut", "gauche bas", "droite haut", "droite bas", "bandeau", "après le bandeau",
    ]


def test_nettoyer_recolle_les_cesures():
    assert nettoyer("une diffi-\nculté   moyenne\n") == "une difficulté moyenne"


def test_titres_illisibles_ecartes():
    assert not est_lisible("\x14)\x12\x11\x07\x10\t\x17\x17")
    assert est_lisible("Hypnos est la voie du sommeil.")


def test_mots_normalise_et_lexique():
    assert mots("Les Réussites particulières") == mots("la réussite particulière")
    assert "median" in " ".join(mots("TMR", avec_lexique=True))
    assert "gardien" in " ".join(mots("le MJ", avec_lexique=True))


def test_decouper_ne_deborde_pas_de_la_page():
    pages = [
        Page(3, 1, ["a" * 700, "b" * 700]),
        Page(4, 2, ["c" * 100]),
    ]
    passages = decouper(pages, "Livre", taille=1000)
    assert [(p.page_livre, len(p.texte)) for p in passages] == [(1, 700), (1, 700), (2, 100)]
    assert passages[0].reference() == "Livre, p. 1"


def _index():
    textes = [
        "Le haut-rêvant monte dans les Terres Médianes en dépensant un point de rêve.",
        "Le combat se joue en rounds ; l'initiative décide qui frappe le premier.",
        "Hypnos est la voie des illusions : le sort trompe les sens de la cible.",
        "La cuisine se juge par la qualité du plat obtenu.",
    ]
    return Index([Passage(i, "Test", i + 1, i + 1, t) for i, t in enumerate(textes)])


def test_bm25_trouve_le_bon_passage():
    idx = _index()
    assert idx.chercher("monter en TMR")[0].passage.page_livre == 1
    assert idx.chercher("lancer une illusion")[0].passage.page_livre == 3
    assert idx.chercher("qualité d'un plat")[0].passage.page_livre == 4


def test_recherche_hybride_avec_plongeur_factice():
    idx = _index()
    # Plongeur factice : un vecteur par thème.
    themes = ["reve", "combat", "illusion", "cuisine"]

    def plonger(textes):
        return [[1.0 if t in x.lower() else 0.0 for t in themes] for x in textes]

    hybride = Index(idx.passages, plonger([p.texte for p in idx.passages]), plonger)
    # Aucun mot en commun avec le passage sur le combat : seul le sens le retrouve.
    assert hybride.chercher("combat : qui agit avant ?")[0].passage.page_livre == 2


def test_fusion_rrf():
    assert fusion_rrf([[1, 2, 3], [2, 3, 1]])[0] == 2


def test_enregistrer_et_charger(tmp_path):
    idx = _index()
    idx.enregistrer(tmp_path)
    recharge = Index.charger(tmp_path)
    assert recharge.passages == idx.passages
    assert recharge.chercher("initiative")[0].passage.page_livre == 2


def test_extraire_un_pdf_a_deux_colonnes(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_textbox(pymupdf.Rect(72, 72, 290, 140), "Gauche, premier paragraphe.")
    page.insert_textbox(pymupdf.Rect(72, 400, 290, 470), "Gauche, second paragraphe.")
    page.insert_textbox(pymupdf.Rect(310, 200, 530, 270), "Droite, troisième paragraphe.")
    chemin = tmp_path / "essai.pdf"
    doc.save(chemin)
    (p,) = extraire(chemin)
    # Lu dans l'ordre des positions verticales, la droite passerait au milieu.
    assert p.blocs == ["Gauche, premier paragraphe.", "Gauche, second paragraphe.", "Droite, troisième paragraphe."]
