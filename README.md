# rdd : assistant de règles pour Rêve de Dragon

Un assistant de joueuse pour Rêve de Dragon. Il cherche dans le livre de règles en citant les pages, et un moteur de règles fait les calculs. Le modèle de langage ne retient rien par cœur.

Ce dépôt ne contient **aucun texte du jeu**. Il faut posséder le livre de règles (réédition Scriptarium), qui reste sur votre ordinateur.

## État

- [x] Table de Résolution, résultats spéciaux, points de qualité
- [ ] Recherche dans le livre (index local)
- [ ] Création et optimisation de personnage
- [ ] Haut-rêve : sorts (Hypnos d'abord), Terres Médianes
- [ ] Interface de discussion avec un modèle local

## Essayer

Il faut Python 3.10 ou plus récent.

```
pip install -e ".[test]"
python -m reve 10 --difficulte -2 --competence -2
```

Exemple de sortie :

```
Ajustement final : difficulté -2 + compétence -2 = -4
Chances : 10 à -4 = 30 %
Seuils : particulière ≤ 06, significative ≤ 15, échec particulier ≥ 86, échec total ≥ 94
Tirage : 12 -> réussite significative
```

Options : `-c` plusieurs fois pour des compétences concurrentes (la plus basse s'applique), `-e` pour l'état général, `-t` pour imposer le tirage.

Tests : `python -m pytest -q`
