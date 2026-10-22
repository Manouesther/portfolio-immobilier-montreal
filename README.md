# Marché immobilier à Montréal — application de données

Application interactive de recherche et d’analyse d’annonces immobilières. Ce dépôt présente ma version personnelle d’un projet initialement réalisé en équipe dans le cadre du cours MIG8110 à l’UQAM. Je l’ai remaniée pour pouvoir expliquer et défendre les choix de données, les traitements, les visualisations et la mise à disposition de l’application.

## Ce que démontre le projet

- Acquisition et actualisation de données d’annonces
- Préparation et stockage en CSV pour la démonstration web
- Analyse descriptive et comparaison des prix
- Visualisations et cartes interactives avec données géographiques
- Automatisation planifiée avec GitHub Actions
- Mise à disposition d’une application web avec Streamlit

## Architecture de cette démo

- Home.py : recherche, filtres et indicateurs
- pages/ : statistiques, cartes et fiche d’annonce
- data/ : fichiers CSV
- scripts/update_data.py : collecte DuProprio
- .github/workflows/update-data.yml : automatisation

La démonstration web lit des CSV versionnés dans GitHub. Elle n’interroge pas PostgreSQL et ne démarre pas Docker. L’entrepôt de données du projet de cours n’est pas déployé dans cette démo. Le workflow de collecte couvre DuProprio, pas Royal LePage.

## Sources et limites

Les annonces sont un échantillon de travail et peuvent être obsolètes. Le script dépend de la structure des pages DuProprio et peut nécessiter une adaptation si celle-ci change. Les résultats ne représentent pas une évaluation exhaustive du marché immobilier.

Le projet initial a été réalisé en équipe; ce dépôt décrit ma version remaniée. Dans mon portfolio, je préciserai les composantes reprises du travail initial et celles que j’ai modifiées ou réalisées, selon leur provenance réelle.

## Exécution locale

Python 3.11 recommandé. Installer les dépendances avec pip install -r requirements.txt, puis lancer streamlit run Home.py.

## Déploiement de test

Streamlit Community Cloud (https://share.streamlit.io) convient à cette application Python/Streamlit. Créer une application depuis ce dépôt, choisir la branche portfolio-streamlit-refresh et le fichier principal Home.py. Les dépendances sont à la racine dans requirements.txt.

## Technologies

Python · Streamlit · pandas · seaborn · Matplotlib · Folium · PyDeck · GeoPy · GitHub Actions
