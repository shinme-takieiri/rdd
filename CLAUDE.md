# Assistant de règles Rêve de Dragon

Langue du projet : français (code, commentaires, messages de commit).

## Règle absolue sur les droits

Ce dépôt est **public**. N'y ajoutez jamais le texte du livre de règles (réédition Scriptarium), ni un extrait long, ni un index, ni des fichiers dérivés du PDF. Ils restent dans `livres/`, `corpus/` ou `index/`, exclus par `.gitignore`. Les règles sont réécrites avec nos propres mots ; une référence de page suffit.

## Structure

- `src/reve/` : moteur de règles déterministe, sans modèle de langage.
- `tests/` : tests tirés des exemples chiffrés du livre. Tout nouveau calcul arrive avec ses tests.

## Commandes

- Tests : `python -m pytest -q`
- Jet en ligne de commande : `PYTHONPATH=src python -m reve 10 -d -2 -c -2`
