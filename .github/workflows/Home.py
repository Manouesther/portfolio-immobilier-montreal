import streamlit as st
import pandas as pd
from babel.numbers import format_currency

st.set_page_config(page_title="Annonces immobilières — Montréal", layout="wide")


def amt(amount):
    return format_currency(amount, "CAD", "#,##0 ¤", "fr_CA", False)


@st.cache_data
def load_data():
    return pd.read_csv("data/logements.csv")


def initialize_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "selected_annonce" not in st.session_state:
        st.session_state.selected_annonce = {}


def display_home_page(data):
    st.markdown(
        "<h1 style='text-align: center; color: #4CAF50;'>Annonces immobilières — Montréal</h1>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Démo basée sur un extrait de données réelles (80 annonces scrapées sur DuProprio "
        "et RoyalLepage). Version adaptée pour Streamlit Community Cloud — voir le README "
        "pour l'architecture complète (Docker, PostgreSQL, entrepôt de données, mise à jour "
        "automatisée)."
    )

    st.subheader("Filtres de recherche")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        prices = st.slider(
            "Prix (CAD)",
            min_value=0,
            max_value=int(data["price"].max()),
            value=[0, int(data["price"].max())],
            step=50000,
            key="price_slider",
        )
    with col2:
        parking = st.number_input("Espace stationnement", value=0, step=1, format="%d")
    with col3:
        bedrooms = st.number_input("Chambres", min_value=0, value=0)

    filtered_data = data[
        (data["price"] >= prices[0])
        & (data["price"] <= prices[1])
        & (data["parking_spaces"] >= parking)
        & (data["bedrooms"].fillna(0) >= bedrooms)
    ].head(20)

    st.subheader("Statistiques générales")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Prix moyen", amt(data["price"].mean()))
    col2.metric("Prix médian", amt(data["price"].median()))
    col3.metric("Nombre d'annonces", f"{len(data)}")
    col4.metric("Chambres moyennes", f"{data['bedrooms'].mean():.1f}")

    display_filtered_data(filtered_data)


def display_filtered_data(filtered_data):
    st.subheader("Annonces disponibles")
    if filtered_data.empty:
        st.info("Aucune annonce ne correspond à ces filtres.")
        return

    for i in range(0, len(filtered_data), 4):
        cols = st.columns(4)
        chunk = filtered_data.iloc[i : i + 4]
        for col, (_, annonce) in zip(cols, chunk.iterrows()):
            with col:
                st.markdown(
                    f"""
                     <div style="background-color: #f7f7f7; border: 1px solid #ddd; border-radius: 10px; padding: 20px; box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1); min-height: 200px;">
                        <a href="{annonce.get('url', '#')}" target="_blank">
                            <div style="font-size: 16px; color: #333; font-weight: bold; margin-bottom: 10px;">{annonce['address']}</div>
                        </a>
                        <div>{amt(annonce['price'])}</div>
                        <div>{int(annonce['bedrooms']) if pd.notna(annonce['bedrooms']) else 'N/A'} chambres, {int(annonce['bathrooms']) if pd.notna(annonce['bathrooms']) else 'N/A'} salles de bain</div>
                    </div>
                """,
                    unsafe_allow_html=True,
                )
                if st.button("Voir les détails", key=f"details_{annonce['url']}", use_container_width=True):
                    st.session_state.selected_annonce = annonce.to_dict()
                    st.session_state.page = "details"
                    st.switch_page("pages/2_Details.py")


def main():
    initialize_session_state()
    data = load_data()
    display_home_page(data)


if __name__ == "__main__":
    main()
