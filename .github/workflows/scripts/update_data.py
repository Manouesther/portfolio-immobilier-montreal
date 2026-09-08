"""
Met à jour data/logements.csv à partir des annonces DuProprio et RoyalLepage.

Ce script est une adaptation du webscraping.py original du projet MIG8110
(qui écrivait dans PostgreSQL) : la logique de scraping et de détection des
changements est conservée, mais la lecture/écriture se fait directement sur
le fichier CSV utilisé par l'application Streamlit.

Conçu pour être exécuté par le workflow GitHub Actions
`.github/workflows/update-data.yml`, sur une base planifiée.
"""

import re
import time
from urllib.parse import quote

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

DATA_PATH = "data/logements.csv"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioBot/1.0)"}


# ---------- Fonctions générales ----------

def define_summary_changes(current_info: pd.DataFrame, old_listings: pd.DataFrame) -> pd.DataFrame:
    df = pd.merge(current_info, old_listings, "outer", "url", suffixes=("", "_old"))

    conditions = [df["price"].isna(), df["price_old"].isna()]
    choices = ["sold", "new"]
    df["action"] = np.select(conditions, choices, "price_change")

    df = df[df["price_old"] != df["price"]][["url", "price", "action"]]
    return df


def coordinates_osm(address):
    """Géocode une adresse via l'API OpenStreetMap Nominatim (gratuite, 1 requête/s max)."""
    encoded_address = quote(address)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&addressdetails=1&limit=1"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Erreur de géocodage pour '{address}': {e}")
        return None, None, None, None

    if not data:
        return None, None, None, None

    latitude = data[0]["lat"]
    longitude = data[0]["lon"]
    address_details = data[0].get("address", {})
    postal_code = address_details.get("postcode")
    fsa = postal_code[:3] if postal_code and len(postal_code) > 3 else None
    return latitude, longitude, postal_code, fsa


def enhance(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute latitude/longitude/code postal/FSA en respectant la limite de 1 req/s de Nominatim."""
    results = []
    for address in df["address"]:
        results.append(coordinates_osm(address))
        time.sleep(1)
    df[["latitude", "longitude", "postal_code", "fsa"]] = pd.DataFrame(results, index=df.index)
    return df


# ---------- DuProprio ----------

def duproprio_summary_raw() -> list:
    raw_listings = []
    nb = float("inf")
    i = 1
    session = requests.Session()

    while len(raw_listings) < nb:
        url = f"https://duproprio.com/fr/rechercher/liste?search=true&cities%5B0%5D=1889&pageNumber={i}"
        soup = BeautifulSoup(session.get(url, headers=HEADERS, timeout=15).text, "html5lib")
        raw_listings.extend(soup.find_all("div", {"class": "search-results-listings-list__container"}))
        count_tag = soup.find("span", {"class": "search-results-listings-header__properties-found__number"})
        if not count_tag:
            break
        nb = int(count_tag.text.strip())
        i += 1

    return raw_listings


def duproprio_summary_info(raw_html: list) -> pd.DataFrame:
    res = []
    for listing in raw_html:
        try:
            url = listing.find("a", {"class": "search-results-listings-list__item-bottom-container"}).get("href")
        except Exception:
            url = None
        try:
            price_text = listing.find("div", {"class": "search-results-listings-list__item-description__price"}).text
            price = int(re.sub(r"\s|\$", "", price_text))
        except Exception:
            price = None
        try:
            address = listing.find("div", {"class": "search-results-listings-list__item-description__address"}).text.strip()
        except Exception:
            address = None
        res.append([url, price, address])
    return pd.DataFrame(res, columns=["url", "price", "address"])


def duproprio_individual_raw(urls) -> list:
    raw_listings = []
    session = requests.Session()
    for url in urls:
        soup = BeautifulSoup(session.get(url, headers=HEADERS, timeout=15).text, "html5lib")
        raw_listings.append([url, soup.find("article", {"class": "listing-tab-content__content"})])
    return raw_listings


def duproprio_individual_info(raw_listing_html: list, listings: pd.DataFrame) -> pd.DataFrame:
    res = []
    for url, content in raw_listing_html:
        if content is None:
            continue
        main_specs = content.find_all("div", {"class": "listing-main-characteristics__label"})
        main_specs = dict(
            re.sub(r"\s+", " ", re.sub("\n", "", x.text).strip()).split(" ", 1)[::-1] for x in main_specs
        )

        def pick(keys, cast=int):
            for k in keys:
                if k in main_specs:
                    try:
                        return cast(main_specs[k])
                    except Exception:
                        return None
            return None

        bedrooms = pick(["chambre", "chambres"])
        bathrooms = pick(["salle de bain", "salles de bain"])
        powder_rooms = pick(["salle d'eau", "salles d'eau"])
        stories = pick(["étage", "étages"])

        other_specs = content.find_all("div", {"class": "listing-box__dotted-row"})
        other_specs = dict(re.sub(r"\n\s*\n*", "|", x.text.strip()).split("|") for x in other_specs)

        try:
            construction_year = int(other_specs["Année de construction"])
        except Exception:
            construction_year = None
        property_style = other_specs.get("Style")
        floors = other_specs.get("Situé à quel étage?")
        try:
            municipal_valuation = sum(
                int(other_specs[k])
                for k in ["Évaluation municipale", "Évaluation municipale du terrain", "Évaluation municipale du bâtiment"]
                if k in other_specs
            )
        except Exception:
            municipal_valuation = None
        try:
            parking_spaces = sum(
                int(other_specs[k])
                for k in ["Nombre de stationnements", "Nombre de stationnements intérieur", "Nombre de stationnements extérieur"]
                if k in other_specs
            )
        except Exception:
            parking_spaces = None

        res.append(
            [url, bedrooms, bathrooms, powder_rooms, stories, construction_year, property_style, floors,
             municipal_valuation, parking_spaces]
        )

    res_df = pd.DataFrame(
        res,
        columns=["url", "bedrooms", "bathrooms", "powder_rooms", "stories", "construction_year",
                 "property_style", "floors", "municipal_valuation", "parking_spaces"],
    )
    return pd.merge(listings, res_df, on="url")


# ---------- Mise à jour du fichier CSV ----------

def apply_changes(current_info: pd.DataFrame, changes: pd.DataFrame, new_details: pd.DataFrame) -> pd.DataFrame:
    updated = current_info.copy()

    sold_urls = changes[changes["action"] == "sold"]["url"]
    updated = updated[~updated["url"].isin(sold_urls)]

    price_changes = changes[changes["action"] == "price_change"]
    for _, row in price_changes.iterrows():
        updated.loc[updated["url"] == row["url"], "price"] = row["price"]

    if not new_details.empty:
        updated = pd.concat([updated, new_details], ignore_index=True)

    return updated


def main():
    current_info = pd.read_csv(DATA_PATH)
    print(f"{len(current_info)} annonces actuellement dans {DATA_PATH}")

    try:
        duproprio_raw = duproprio_summary_raw()
        duproprio_info = duproprio_summary_info(duproprio_raw)
        print(f"{len(duproprio_info)} annonces trouvées sur DuProprio")
    except Exception as e:
        print(f"Scraping DuProprio impossible ({e}) — étape ignorée pour cette exécution.")
        duproprio_info = pd.DataFrame(columns=["url", "price", "address"])

    if duproprio_info.empty:
        print("Aucune donnée DuProprio récupérée, fin du script.")
        return

    changes = define_summary_changes(duproprio_info, current_info[["url", "price"]])
    print(f"{len(changes)} changement(s) détecté(s) : "
          f"{(changes['action'] == 'new').sum()} nouvelle(s), "
          f"{(changes['action'] == 'sold').sum()} vendue(s), "
          f"{(changes['action'] == 'price_change').sum()} prix modifié(s)")

    new_urls = changes[changes["action"] == "new"]["url"]
    new_details = pd.DataFrame()
    if len(new_urls) > 0:
        try:
            raw_individual = duproprio_individual_raw(new_urls)
            new_details = duproprio_individual_info(raw_individual, duproprio_info[duproprio_info["url"].isin(new_urls)])
            new_details = enhance(new_details)
        except Exception as e:
            print(f"Erreur lors de la récupération des détails des nouvelles annonces : {e}")
            new_details = pd.DataFrame()

    updated = apply_changes(current_info, changes, new_details)
    updated.to_csv(DATA_PATH, index=False)
    print(f"{len(updated)} annonces sauvegardées dans {DATA_PATH}")


if __name__ == "__main__":
    main()
