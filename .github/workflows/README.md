# Annonces immobilières — Montréal (version portfolio)

Application Streamlit de recherche et d'analyse d'annonces immobilières à
Montréal, avec cartes interactives et statistiques.

## À propos de cette version

Ceci est une **version adaptée pour Streamlit Community Cloud** d'un projet
de data engineering plus large, réalisé en équipe dans le cadre du cours
MIG8110 (UQAM). Le projet original utilise Docker, PostgreSQL (base de
données + entrepôt de données en schéma en étoile) et un module de
web scraping avec mise à jour automatisée (DuProprio, RoyalLepage).

Streamlit Community Cloud ne pouvant pas exécuter de conteneurs Docker ni de
base de données persistante, cette version :
- lit les données depuis des fichiers CSV statiques (un extrait réel de 80
  annonces, exporté depuis la base de données du projet original) plutôt que
  depuis PostgreSQL ;
- conserve toute la logique d'analyse, de visualisation et de cartographie
  de l'application originale.

**Le projet complet (Docker, PostgreSQL, entrepôt de données, web scraping
automatisé) est disponible ici : [lien vers le dépôt complet — à ajouter]**

## Contributions

- Application originale et pipeline de données : projet d'équipe, cours
  MIG8110 (UQAM)
- Carte de densité (`HeatMap` / `MarkerCluster`) dans la page Statistiques :
  contribution personnelle, adaptée de la version explorée dans
  `home esther.py` du projet original

## Structure

```
immobilier-portfolio/
├── Home.py                     # Recherche et filtrage des annonces
├── requirements.txt
├── data/
│   ├── logements.csv
│   ├── bornes_recharge.csv
│   └── stationnements.csv
└── pages/
    ├── 1_Statistiques.py       # Visualisations, carte de densité, services à proximité
    └── 2_Details.py            # Détails d'une annonce sélectionnée
```

## Tester en local

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Déployer sur Streamlit Community Cloud

1. Créez un dépôt GitHub et poussez-y ce dossier (utilisez l'option
   "uploading an existing file" sur GitHub si vous préférez ne pas utiliser
   la ligne de commande).
2. Allez sur https://share.streamlit.io, connectez votre compte GitHub.
3. "New app" → sélectionnez le dépôt → fichier principal `Home.py` → Deploy.

## Limites de cette version de démonstration

- Les lignes et arrêts de métro ne sont pas inclus dans cet extrait de
  données (fichiers non fournis) ; les sections correspondantes du projet
  original ont donc été retirées de cette version.
- Le scraping automatisé (voir ci-dessous) ne couvre que DuProprio pour
  l'instant. RoyalLepage a été laissé de côté dans un premier temps car son
  URL de recherche originale contient un jeton propre à une session, plus
  fragile à maintenir — le même principe pourrait être ajouté plus tard en
  s'inspirant du code original (`update-db-dw/webscraping.py`).

## Mise à jour automatisée des données (GitHub Actions)

Un workflow GitHub Actions (`.github/workflows/update-data.yml`) relance le
scraping DuProprio chaque jour à 9h00 UTC, détecte les changements (nouvelle
annonce, annonce vendue, changement de prix), et met à jour
`data/logements.csv` directement dans le dépôt. Ce commit déclenche ensuite
automatiquement un redéploiement de l'app sur Streamlit Community Cloud.

### Comment ça fonctionne, concrètement

1. **Le déclencheur (`on:`)** — le workflow se lance seul selon l'horaire
   `cron`, ou manuellement depuis l'onglet **Actions** du dépôt GitHub
   (bouton **Run workflow**) — pratique pour tester sans attendre le
   lendemain.
2. **Les étapes (`steps:`)** — GitHub prépare une machine virtuelle
   temporaire, y copie votre dépôt, installe Python et les dépendances,
   puis exécute `scripts/update_data.py`.
3. **Le commit automatique** — si le script a modifié le fichier CSV, les
   dernières étapes du workflow commettent et poussent ce changement, en
   utilisant un jeton d'accès (`GITHUB_TOKEN`) que GitHub fournit
   automatiquement à chaque exécution — aucune configuration de mot de
   passe ou de clé nécessaire.

### Pour l'activer

Aucune étape supplémentaire : une fois ce dossier poussé sur GitHub, le
workflow est actif automatiquement (GitHub détecte tout fichier dans
`.github/workflows/`). Vous pouvez suivre son exécution dans l'onglet
**Actions** du dépôt, et consulter les logs de chaque étape en cas
d'erreur (utile si la structure HTML d'un site change et casse le
scraping — un risque normal et courant avec le web scraping).

