import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import math
from babel.numbers import format_currency

st.set_page_config(page_title="Détails | Montréal", page_icon="⌂", layout="wide")


def amt(amount):
    return format_currency(amount, "CAD", "#,##0 ¤", "fr_CA", False)


def my_int(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "N/A"
    return int(x)


@st.cache_data
def load_data():
    logements = pd.read_csv("data/logements.csv")
    bornes_recharge = pd.read_csv("data/bornes_recharge.csv")
    stationnements = pd.read_csv("data/stationnements.csv")
    return logements, bornes_recharge, stationnements


def generate_price_comparison(logements, fsa, current_price):
    same_fsa = logements[logements["fsa"] == fsa]
    avg_price = same_fsa["price"].mean() if not same_fsa.empty else 0

    fig, ax = plt.subplots(figsize=(3, 2))
    sns.barplot(x=["Prix", "Moyenne zone"], y=[current_price, avg_price], palette="coolwarm", ax=ax)
    ax.set_title(f"Prix — zone {fsa}")
    ax.set_ylabel("Prix (CAD)")
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close(fig)
    return buffer


def display_annonce_details(annonce, logements):
    price_buffer = generate_price_comparison(logements, annonce.get("fsa"), annonce.get("price", 0))
    price_encoded = base64.b64encode(price_buffer.read()).decode("utf-8")

    st.markdown("<h2 style='text-align: center; color: #4CAF50;'>Détails de l'annonce</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.5, 1])
    with col1:
        st.markdown(
            f"""
            <div style="background-color: #f9f9f9;border: 1px solid #ddd;border-radius: 10px; padding: 15px;">
                <p><strong>Prix (CAD) :</strong> {amt(annonce.get('price', 0))}</p>
                <p><strong>Adresse :</strong> {annonce.get('address', 'N/A')}</p>
                <p><strong>Chambres :</strong> {my_int(annonce.get('bedrooms'))} |
                   <strong>Salles de bain :</strong> {my_int(annonce.get('bathrooms'))}</p>
                <p><strong>Salles d'eau :</strong> {my_int(annonce.get('powder_rooms'))} |
                   <strong>Niveau :</strong> {my_int(annonce.get('stories'))}</p>
                <p><strong>Année de construction :</strong> {my_int(annonce.get('construction_year'))}</p>
                <p><strong>Style de propriété :</strong> {annonce.get('property_style', 'N/A')}</p>
                <p><strong>Évaluation municipale (CAD) :</strong> {amt(annonce.get('municipal_valuation', 0)) if annonce.get('municipal_valuation') else 'N/A'}</p>
                <p><strong>Espaces de stationnement :</strong> {my_int(annonce.get('parking_spaces'))}</p>
                <p><strong>Superficie habitable (m²) :</strong> {annonce.get('living_area', 'N/A')}</p>
                <p><strong>Superficie du terrain (m²) :</strong> {annonce.get('land_area', 'N/A')}</p>
                <p><strong>Code postal :</strong> {annonce.get('postal_code', 'N/A')}</p>
                <p><a href="{annonce.get('url', '#')}" target="_blank">Voir l'annonce complète</a></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.image(f"data:image/png;base64,{price_encoded}")


def display_map(annonce, bornes_recharge, stationnements):
    fsa = annonce.get("fsa")
    property_location = pd.DataFrame(
        [{"latitude": annonce["latitude"], "longitude": annonce["longitude"], "color": [0, 0, 0]}]
    )

    map_data = property_location.copy()
    counts = {"Stationnements": 0, "Bornes de recharge": 0}

    nearby_parking = stationnements[stationnements["FSA"] == fsa]
    if not nearby_parking.empty:
        p = nearby_parking.rename(columns={"Latitude": "latitude", "Longitude": "longitude"})[["latitude", "longitude"]]
        p["color"] = [[255, 0, 0]] * len(p)
        map_data = pd.concat([map_data, p], ignore_index=True)
        counts["Stationnements"] = len(p)

    nearby_bornes = bornes_recharge[bornes_recharge["FSA"] == fsa]
    if not nearby_bornes.empty:
        b = nearby_bornes.rename(columns={"Latitude": "latitude", "Longitude": "longitude"})[["latitude", "longitude"]]
        b["color"] = [[0, 255, 0]] * len(b)
        map_data = pd.concat([map_data, b], ignore_index=True)
        counts["Bornes de recharge"] = len(b)

    st.subheader("Carte de localisation")
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[longitude, latitude]",
        get_color="color",
        get_radius=50,
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=property_location["latitude"].iloc[0],
        longitude=property_location["longitude"].iloc[0],
        zoom=14,
    )
    st.pydeck_chart(pdk.Deck(layers=[scatter_layer], initial_view_state=view_state))

    st.markdown(
        f"Stationnements à proximité (zone {fsa}) : **{counts['Stationnements']}** — "
        f"Bornes de recharge à proximité : **{counts['Bornes de recharge']}**"
    )


def main():
    logements, bornes_recharge, stationnements = load_data()

    if "selected_annonce" not in st.session_state or not st.session_state.selected_annonce:
        st.warning("Aucune annonce sélectionnée. Retournez à la page d'accueil pour en choisir une.")
        if st.button("Retour aux annonces"):
            st.switch_page("Home.py")
        st.stop()

    annonce = st.session_state.selected_annonce
    display_annonce_details(annonce, logements)
    display_map(annonce, bornes_recharge, stationnements)

    if st.button("Retour aux annonces"):
        st.session_state.pop("selected_annonce", None)
        st.switch_page("Home.py")


if __name__ == "__main__":
    main()
