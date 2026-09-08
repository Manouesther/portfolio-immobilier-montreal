import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import folium_static
from geopy.distance import geodesic

st.set_page_config(page_title="Statistiques", layout="wide")


@st.cache_data
def load_data():
    logements = pd.read_csv("data/logements.csv")
    bornes_recharge = pd.read_csv("data/bornes_recharge.csv")
    stationnements = pd.read_csv("data/stationnements.csv")
    return logements, bornes_recharge, stationnements


def display_visualizations(data):
    st.subheader("Visualisations des données")

    st.markdown("#### Prix moyen au m²")
    valid = data.dropna(subset=["living_area"]).copy()
    valid["prix_m2"] = valid["price"] / valid["living_area"]
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(valid["prix_m2"], bins=20, kde=True, color="green", ax=ax)
    ax.set_title("Distribution des prix moyens au m²")
    st.pyplot(fig)
    st.caption(
        "Répartition des prix au m² (prix total divisé par la surface habitable). "
        f"Basé sur {len(valid)} annonces disposant d'une surface habitable connue."
    )

    st.markdown("#### Prix moyen par zone (code postal)")
    price_by_zone = data.groupby("postal_code")["price"].mean().reset_index().sort_values("price")
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(x="postal_code", y="price", data=price_by_zone, palette="viridis", ax=ax)
    ax.set_title("Prix moyen par code postal")
    ax.set_xlabel("Code postal")
    ax.set_ylabel("Prix moyen (CAD)")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    st.pyplot(fig)

    st.markdown("#### Répartition des annonces par zone (FSA)")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.countplot(x="fsa", data=data, palette="Set2", ax=ax, order=data["fsa"].value_counts().index)
    ax.set_title("Nombre d'annonces par FSA")
    ax.set_xlabel("FSA (zone de tri d'acheminement)")
    ax.set_ylabel("Nombre de logements")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
    st.pyplot(fig)


def display_heatmap(data):
    # Densité des annonces — carte de chaleur (contribution personnelle, ajoutée à
    # la version originale du projet d'équipe)
    st.subheader("Carte de densité des annonces")
    st.caption("Carte de chaleur et regroupement des annonces par secteur.")

    valid = data.dropna(subset=["latitude", "longitude"])
    center = [valid["latitude"].mean(), valid["longitude"].mean()]
    m = folium.Map(location=center, zoom_start=12)

    HeatMap(valid[["latitude", "longitude"]].values.tolist(), radius=18).add_to(m)

    cluster = MarkerCluster().add_to(m)
    for _, row in valid.iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            popup=f"{row['address']}",
        ).add_to(cluster)

    folium_static(m)


def calculate_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).km


def find_nearby_services(lat, lon, distance_km, bornes_recharge, stationnements):
    nearby = []
    for _, row in bornes_recharge.dropna(subset=["Latitude", "Longitude"]).iterrows():
        d = calculate_distance(lat, lon, row["Latitude"], row["Longitude"])
        if d <= distance_km:
            nearby.append({"type": "Borne de recharge", "lat": row["Latitude"], "lon": row["Longitude"], "distance": d})
    for _, row in stationnements.dropna(subset=["Latitude", "Longitude"]).iterrows():
        d = calculate_distance(lat, lon, row["Latitude"], row["Longitude"])
        if d <= distance_km:
            nearby.append({"type": "Stationnement", "lat": row["Latitude"], "lon": row["Longitude"], "distance": d})
    return nearby


def display_map_with_services(data, bornes_recharge, stationnements):
    st.subheader("Carte des annonces et services à proximité")

    options = data[["address", "latitude", "longitude"]].dropna().reset_index(drop=True)
    selected = st.selectbox("Choisissez un logement :", options["address"])
    coord = options[options["address"] == selected].iloc[0]

    distance_km = st.slider("Distance de recherche (km) :", min_value=1, max_value=10, value=2)

    m = folium.Map(location=[coord["latitude"], coord["longitude"]], zoom_start=15)
    folium.Marker(
        [coord["latitude"], coord["longitude"]],
        popup=f"Logement : {selected}",
        icon=folium.Icon(color="blue"),
    ).add_to(m)

    nearby = find_nearby_services(coord["latitude"], coord["longitude"], distance_km, bornes_recharge, stationnements)
    for service in nearby:
        color = "green" if service["type"] == "Borne de recharge" else "red"
        folium.Marker(
            [service["lat"], service["lon"]],
            popup=f"{service['type']} — {service['distance']:.2f} km",
            icon=folium.Icon(color=color),
        ).add_to(m)

    folium_static(m)
    st.caption(f"{len(nearby)} service(s) trouvé(s) dans un rayon de {distance_km} km.")


def main():
    data, bornes_recharge, stationnements = load_data()
    display_visualizations(data)
    st.divider()
    display_heatmap(data)
    st.divider()
    display_map_with_services(data, bornes_recharge, stationnements)


if __name__ == "__main__":
    main()
