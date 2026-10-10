
import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote
from io import BytesIO

st.set_page_config(
    page_title="Wine Sales Prospector",
    page_icon="🍷",
    layout="wide"
)

st.title("🍷 Wine Sales Prospector")
st.write("Prospection commerciale — Baja California Sur")

VILLES = {
    "La Paz": ["la paz"],
    "Todos Santos": ["todos santos"],
    "Cabo San Lucas": ["cabo san lucas"],
    "San José del Cabo": ["san jose del cabo", "san josé del cabo"],
    "Toutes les villes": []
}

CATEGORIES = {
    "Restaurants": ["restaurante", "restaurantes"],
    "Hôtels": ["hotel", "hoteles"],
    "Bars et bars à vin": ["bar", "vinoteca", "enoteca"],
    "Cavistes et magasins de vin": [
        "vinateria", "vinatería", "vinos", "licores"
    ],
    "Distributeurs": ["distribuidora", "mayoreo"],
    "Épiceries fines": ["delicatessen", "productos gourmet"]
}

def score_prospect(nom, activite, ville):
    texte = f"{nom} {activite}".lower()
    score = 35
    raisons = []

    if any(x in texte for x in [
        "gourmet", "fine dining", "gastronom",
        "gastronómico", "gastronomico"
    ]):
        score += 30
        raisons.append("Positionnement gastronomique")

    if any(x in texte for x in [
        "hotel boutique", "boutique hotel",
        "resort", "hotel", "hotel"
    ]):
        score += 20
        raisons.append("Clientèle hôtelière potentielle")

    if any(x in texte for x in [
        "vino", "vinoteca", "vinatería", "vinateria",
        "enoteca", "licores"
    ]):
        score += 25
        raisons.append("Activité liée au vin ou aux boissons")

    if any(x in texte for x in [
        "restaurante", "restaurant"
    ]):
        score += 15
        raisons.append("Établissement de restauration")

    score = min(score, 100)

    if score >= 70:
        niveau = "Priorité élevée"
    elif score >= 50:
        niveau = "Priorité moyenne"
    else:
        niveau = "À qualifier"

    return score, niveau, ", ".join(raisons) or (
        "Vérifier la carte et le positionnement"
    )


@st.cache_data(ttl=3600, show_spinner=False)
def rechercher_inegi(terme, token):
    url = (
        "https://www.inegi.org.mx/app/api/denue/v1/consulta/"
        f"buscarEntidad/{quote(terme, safe='')}/03/1/100/"
        f"{quote(token, safe='')}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    donnees = response.json()
    return donnees if isinstance(donnees, list) else []

  
st.sidebar.header("Recherche")
st.sidebar.write("Répertoire officiel DENUE — INEGI")

token = st.sidebar.text_input(
    "Clé API INEGI",
    type="password",
    help="Obtiens gratuitement une clé auprès de l'INEGI."
)

ville = st.sidebar.selectbox("Ville", list(VILLES.keys()))
categorie = st.sidebar.selectbox(
    "Type d'établissement", list(CATEGORIES.keys())
)

if st.sidebar.button("Rechercher les établissements", type="primary"):
    if not token.strip():
        st.sidebar.error(
            "Il faut une clé API INEGI pour lancer la recherche."
        )
    else:
        resultats = []
        erreurs = []

        with st.spinner("Recherche dans le répertoire INEGI..."):
            for terme in CATEGORIES[categorie]:
                try:
                    resultats.extend(
                        rechercher_inegi(terme, token.strip())
                    )
                except Exception as e:
                    erreurs.append(str(e))

        uniques = {}
        for item in resultats:
            identifiant = str(
                item.get("Id") or item.get("Nombre", "")
            )
            if identifiant:
                uniques[identifiant] = item

        lignes = []
        mots_ville = VILLES[ville]

        for item in uniques.values():
            nom = str(item.get("Nombre", ""))
            activite = str(item.get("Clase_actividad", ""))
            localite = str(item.get("Localidad", ""))
            municipio = str(item.get("Municipio", ""))
            adresse = str(item.get("Ubicacion", ""))
            zone = f"{localite} {municipio} {adresse}".lower()

            if mots_ville and not any(
                mot in zone for mot in mots_ville
            ):
                continue

            score, niveau, raison = score_prospect(
                nom, activite, ville
            )

            lignes.append({
                "Établissement": nom,
                "Ville / zone": localite or municipio,
                "Activité": activite,
                "Score estimé": score,
                "Priorité": niveau,
                "Pourquoi": raison,
                "Adresse": adresse,
                "Téléphone": item.get("Telefono", ""),
                "Site web": item.get("Sitio_internet", ""),
                "Identifiant INEGI": item.get("Id", "")
            })

        st.session_state["resultats"] = lignes
        st.session_state["recherche_ville"] = ville
        st.session_state["recherche_categorie"] = categorie

        if erreurs and not lignes:
            st.error(
                "La recherche n'a pas abouti. Vérifie ta clé API "
                "et la disponibilité du service INEGI."
            )
            st.caption(erreurs[0])

if "resultats" in st.session_state:
    df = pd.DataFrame(st.session_state["resultats"])

    st.subheader("Résultats de la recherche")
    st.caption(
        f"{len(df)} établissement(s) trouvé(s). "
        "Le score est indicatif et ne garantit pas un achat."
    )

    if not df.empty:
        minimum = st.slider(
            "Score commercial minimum",
            min_value=0, max_value=100, value=0
        )
        filtres = df[df["Score estimé"] >= minimum]
        filtres = filtres.sort_values(
            "Score estimé", ascending=False
        )

        a, b, c = st.columns(3)
        a.metric("Établissements", len(filtres))
        b.metric(
            "Priorité élevée",
            int((filtres["Priorité"] == "Priorité élevée").sum())
        )
        c.metric(
            "Score moyen",
            round(filtres["Score estimé"].mean(), 1)
        )

        st.dataframe(
            filtres,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Site web": st.column_config.LinkColumn(
                    "Site web", display_text="Ouvrir le site"
                )
            }
        )

        st.download_button(
            "Télécharger les résultats en CSV",
            data=filtres.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="prospects_vins.csv",
            mime="text/csv"
        )
    else:
        st.info(
            "Aucun établissement trouvé pour ces critères. "
            "Essaie une autre catégorie ou une autre ville."
        )

st.divider()
st.caption(
    "Les données proviennent du répertoire interrogé. "
    "Le classement est une première estimation automatique : "
    "vérifie les informations et la carte des vins avant une visite."
)
