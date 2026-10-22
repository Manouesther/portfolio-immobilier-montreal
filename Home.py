import pandas as pd
import streamlit as st
from babel.numbers import format_currency

st.set_page_config(page_title="Marché immobilier | Montréal", page_icon="⌂", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;color:#142321}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.035em}
.block-container{max-width:1260px;padding-top:2.1rem}
[data-testid="stMetric"]{background:#f4f6f2;border:1px solid #e7ebe3;padding:1rem 1.15rem;border-radius:16px}
div.stButton>button{border-radius:999px;border:1px solid #d9e0d4;font-weight:600}
[data-testid="stSidebar"]{background:#f7f8f5}
</style>""",unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv("data/logements.csv")

def amt(value):
    return format_currency(value,"CAD","#,##0 ¤","fr_CA",False)

def main():
    data=load_data()
    if data.empty:
        st.warning("Aucune annonce n’est disponible.")
        return
    st.markdown("""<section style="padding:2.2rem 2.4rem;border-radius:24px;background:#142321;color:#fff;margin-bottom:1.5rem">
    <div style="color:#b9f36a;font-size:.78rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase">Données immobilières · Montréal</div>
    <h1 style="color:#fff;margin:.65rem 0 .25rem;font-size:2.6rem">Le marché, en perspective.</h1>
    <p style="color:#d1d8d1;margin:0;max-width:680px">Explorez les annonces, comparez les prix et découvrez leur répartition géographique.</p></section>""",unsafe_allow_html=True)
    st.caption("Démo portfolio : données d’annonces échantillonnées et conservées en CSV. Voir le README pour le périmètre et les limites.")
    st.subheader("Explorer les annonces")
    c1,c2,c3=st.columns([2,1,1])
    with c1:
        limits=st.slider("Prix (CAD)",0,int(data.price.max()),(0,int(data.price.max())),step=50000)
    with c2:
        parking=st.number_input("Stationnements minimum",min_value=0,value=0,step=1)
    with c3:
        bedrooms=st.number_input("Chambres minimum",min_value=0,value=0)
    filtered=data[(data.price>=limits[0])&(data.price<=limits[1])&(data.parking_spaces.fillna(0)>=parking)&(data.bedrooms.fillna(0)>=bedrooms)].head(24)
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Prix moyen",amt(data.price.mean()))
    m2.metric("Prix médian",amt(data.price.median()))
    m3.metric("Annonces",f"{len(data):,}".replace(",", " "))
    m4.metric("Chambres moyennes",f"{data.bedrooms.mean():.1f}")
    st.divider()
    st.subheader(f"Résultats · {len(filtered)} annonces")
    if filtered.empty:
        st.info("Aucune annonce ne correspond à ces filtres.")
        return
    for start in range(0,len(filtered),3):
        cols=st.columns(3)
        for col,(_,row) in zip(cols,filtered.iloc[start:start+3].iterrows()):
            with col:
                st.markdown(f"""<article style="padding:1.2rem;border:1px solid #e7ebe3;border-radius:18px;margin:.3rem 0 1rem;background:#fff;min-height:155px">
                <div style="font-weight:700;font-size:1rem;color:#142321">{row.get('address','Adresse non précisée')}</div>
                <div style="font-size:1.45rem;font-weight:800;margin:.7rem 0;color:#38572f">{amt(row.price)}</div>
                <div style="color:#66736d">{int(row.bedrooms) if pd.notna(row.bedrooms) else '—'} ch. · {int(row.bathrooms) if pd.notna(row.bathrooms) else '—'} sdb · {int(row.parking_spaces) if pd.notna(row.parking_spaces) else '—'} stationnement(s)</div></article>""",unsafe_allow_html=True)
                if st.button("Voir la fiche",key=f"details_{row.url}",use_container_width=True):
                    st.session_state.selected_annonce=row.to_dict()
                    st.switch_page("pages/2_Details.py")

if __name__=="__main__":
    main()
