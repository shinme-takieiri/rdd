# rdd : assistant de règles pour Rêve de Dragon

Un assistant de joueuse pour Rêve de Dragon. Il cherche dans le livre de règles en citant les pages, et un moteur de règles fait les calculs. Le modèle de langage ne retient rien par cœur.

Ce dépôt ne contient **aucun texte du jeu**. Il faut posséder le livre de règles (réédition Scriptarium), qui reste sur votre ordinateur.

## État

- [x] Table de Résolution, résultats spéciaux, points de qualité
- [x] Recherche dans le livre (index local, par mots-clés, et par le sens avec Ollama)
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

## Chercher dans le livre

Le livre reste sur votre ordinateur. Copiez votre PDF dans un dossier `livres/` (exclu du dépôt), puis :

```
pip install -e ".[recherche]"
python -m reve.recherche indexer livres/Rdd.pdf --decalage 2 --source "Rêve de Dragon"
python -m reve.recherche chercher "comment lancer un sort d'illusion"
```

`--decalage 2` aligne les numéros de page sur ceux imprimés dans la réédition Scriptarium. L'index est écrit dans `index/`, lui aussi exclu du dépôt.

### Recherche par le sens (recommandée, sur le PC avec la carte graphique)

La recherche par mots-clés rate les questions formulées autrement que le livre (« qui agit en premier ? » au lieu d'« initiative »). Pour l'ajouter :

1. Installer [Ollama](https://ollama.com), puis `ollama pull bge-m3`.
2. Reconstruire l'index avec `--sens` : `python -m reve.recherche indexer livres/Rdd.pdf --decalage 2 --source "Rêve de Dragon" --sens`

Les deux recherches sont alors combinées automatiquement. Rien ne quitte l'ordinateur.

### Mesurer la qualité

`python -m reve.recherche evaluer` pose les questions de `evaluation/questions_rdd.json` et vérifie que la bonne page sort dans les 5 premiers résultats. Ce fichier ne contient que des questions et des numéros de page.
