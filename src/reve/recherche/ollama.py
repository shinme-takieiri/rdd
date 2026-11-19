"""Plongements vectoriels via un serveur Ollama local (optionnel).

Installer Ollama, puis : ``ollama pull bge-m3`` (modèle multilingue, bon en français).
Rien ne quitte l'ordinateur.
"""

from __future__ import annotations

import json
import urllib.request

ADRESSE = "http://localhost:11434"
MODELE = "bge-m3"


def plongeur(modele: str = MODELE, adresse: str = ADRESSE, lot: int = 32):
    def plonger(textes: list[str]) -> list[list[float]]:
        vecteurs: list[list[float]] = []
        for i in range(0, len(textes), lot):
            corps = json.dumps({"model": modele, "input": textes[i : i + lot]}).encode()
            requete = urllib.request.Request(
                f"{adresse}/api/embed", corps, {"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(requete, timeout=300) as reponse:
                vecteurs += json.loads(reponse.read())["embeddings"]
        return vecteurs

    return plonger


def disponible(adresse: str = ADRESSE) -> bool:
    try:
        with urllib.request.urlopen(f"{adresse}/api/tags", timeout=2):
            return True
    except OSError:
        return False
