"""Découpage en passages et index de recherche local.

Deux moteurs, combinés quand les deux sont disponibles :

* **mots-clés** (BM25), sans aucune dépendance, avec une normalisation
  adaptée au français et un petit lexique du jeu (TMR, gardien des rêves…) ;
* **sens** (plongements vectoriels) via Ollama, optionnel.

Les classements sont fusionnés par rang réciproque (RRF).
L'index est écrit dans un dossier local, exclu du dépôt.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from .extraction import Page

TAILLE_PASSAGE = 1200  # caractères, environ 200 mots

# Mots trop fréquents pour aider à la recherche.
MOTS_VIDES = set(
    """a au aux avec ce ces dans de des du elle en et eux il ils je la le les leur lui ma mais me meme
    mes moi mon ne nos notre nous on ou par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un
    une vos votre vous c d j l m n s t y est sont ete etre avoir a ont fait peut plus si tout tous toute
    toutes cette cet comme dont ainsi alors aussi donc ni car bien tres sans sous entre deja encore""".split()
)

# Lexique du jeu : abréviations et synonymes, avec nos propres mots.
LEXIQUE = {
    "tmr": "terres medianes reve",
    "mj": "gardien reves",
    "meneur": "gardien reves",
    "hr": "haut reve",
    "pr": "points reve",
    "xp": "experience",
    "pv": "points vie",
    "endu": "endurance",
    "part": "particuliere",
    "sign": "significative",
    "illusion": "hypnos",
    "illusions": "hypnos",
}


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def racine(mot: str) -> str:
    """Racinisation légère du français : pluriels et féminins."""
    if len(mot) > 3 and mot[-1] in "sx":
        mot = mot[:-1]
    for fin, remplace in (("ere", "er"), ("ee", "e"), ("euse", "eur"), ("ive", "if"), ("elle", "el")):
        if len(mot) > len(fin) + 2 and mot.endswith(fin):
            return mot[: -len(fin)] + remplace
    if len(mot) > 4 and mot.endswith("e"):
        mot = mot[:-1]
    return mot


def mots(texte: str, avec_lexique: bool = False) -> list[str]:
    bruts = re.findall(r"[a-z0-9]+", _sans_accents(texte.lower()))
    if avec_lexique:
        bruts = [m for b in bruts for m in ([b, *LEXIQUE[b].split()] if b in LEXIQUE else [b])]
    return [racine(m) for m in bruts if m not in MOTS_VIDES and len(m) > 1]


@dataclass(frozen=True)
class Passage:
    id: int
    source: str
    page_pdf: int
    page_livre: int | None
    texte: str

    def reference(self) -> str:
        page = self.page_livre if self.page_livre is not None else f"PDF {self.page_pdf}"
        return f"{self.source}, p. {page}"


def decouper(pages: list[Page], source: str, taille: int = TAILLE_PASSAGE) -> list[Passage]:
    """Regroupe les blocs de chaque page en passages d'environ ``taille`` caractères.

    Un passage ne déborde jamais sur la page suivante : la référence reste exacte.
    """
    passages: list[Passage] = []
    for page in pages:
        courant: list[str] = []
        for bloc in page.blocs:
            if courant and sum(len(b) for b in courant) + len(bloc) > taille:
                passages.append(Passage(len(passages), source, page.numero_pdf, page.numero_livre, " ".join(courant)))
                courant = []
            courant.append(bloc)
        if courant:
            passages.append(Passage(len(passages), source, page.numero_pdf, page.numero_livre, " ".join(courant)))
    return [p for p in passages if len(p.texte) >= 40]


class BM25:
    def __init__(self, documents: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.k1, self.b = k1, b
        self.frequences = [Counter(d) for d in documents]
        self.longueurs = [len(d) for d in documents]
        self.longueur_moyenne = sum(self.longueurs) / max(1, len(documents))
        nb_docs_par_mot = Counter(m for d in documents for m in set(d))
        n = len(documents)
        self.idf = {m: math.log(1 + (n - df + 0.5) / (df + 0.5)) for m, df in nb_docs_par_mot.items()}

    def scores(self, requete: list[str]) -> list[float]:
        resultat = []
        for freq, longueur in zip(self.frequences, self.longueurs):
            s = 0.0
            norme = self.k1 * (1 - self.b + self.b * longueur / self.longueur_moyenne)
            for m in requete:
                f = freq.get(m)
                if f:
                    s += self.idf[m] * f * (self.k1 + 1) / (f + norme)
            resultat.append(s)
        return resultat


def _cosinus(a: list[float], b: list[float]) -> float:
    produit = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return produit / (na * nb) if na and nb else 0.0


def fusion_rrf(classements: list[list[int]], k: int = 60) -> list[int]:
    scores: Counter[int] = Counter()
    for classement in classements:
        for rang, ident in enumerate(classement):
            scores[ident] += 1 / (k + rang + 1)
    return [i for i, _ in scores.most_common()]


@dataclass
class Resultat:
    passage: Passage
    rang: int


class Index:
    FICHIER_PASSAGES = "passages.jsonl"
    FICHIER_VECTEURS = "vecteurs.json"

    def __init__(self, passages: list[Passage], vecteurs: list[list[float]] | None = None, plongeur=None):
        self.passages = passages
        self.vecteurs = vecteurs
        self.plongeur = plongeur
        self.bm25 = BM25([mots(p.texte) for p in passages])

    # --- Persistance -----------------------------------------------------
    def enregistrer(self, dossier: str | Path) -> None:
        dossier = Path(dossier)
        dossier.mkdir(parents=True, exist_ok=True)
        with open(dossier / self.FICHIER_PASSAGES, "w", encoding="utf-8") as f:
            for p in self.passages:
                f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
        if self.vecteurs is not None:
            (dossier / self.FICHIER_VECTEURS).write_text(json.dumps(self.vecteurs), encoding="utf-8")

    @classmethod
    def charger(cls, dossier: str | Path, plongeur=None) -> "Index":
        dossier = Path(dossier)
        with open(dossier / cls.FICHIER_PASSAGES, encoding="utf-8") as f:
            passages = [Passage(**json.loads(ligne)) for ligne in f if ligne.strip()]
        chemin_vecteurs = dossier / cls.FICHIER_VECTEURS
        vecteurs = json.loads(chemin_vecteurs.read_text(encoding="utf-8")) if chemin_vecteurs.exists() else None
        return cls(passages, vecteurs, plongeur if vecteurs is not None else None)

    # --- Recherche ---------------------------------------------------------
    def chercher(self, question: str, n: int = 5) -> list[Resultat]:
        scores = self.bm25.scores(mots(question, avec_lexique=True))
        par_mots = [i for i in sorted(range(len(scores)), key=lambda i: -scores[i]) if scores[i] > 0][:50]
        classements = [par_mots]
        if self.vecteurs is not None and self.plongeur is not None:
            q = self.plongeur([question])[0]
            sims = [_cosinus(q, v) for v in self.vecteurs]
            classements.append(sorted(range(len(sims)), key=lambda i: -sims[i])[:50])
        ordre = fusion_rrf(classements) if len(classements) > 1 else par_mots
        return [Resultat(self.passages[i], r + 1) for r, i in enumerate(ordre[:n])]
