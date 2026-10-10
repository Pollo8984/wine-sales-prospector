import streamlit as st

st.set_page_config(
    page_title="Wine Sales Prospector",
    page_icon="🍷",
    layout="wide"
)

st.title("🍷 Wine Sales Prospector")
st.subheader("Prospection commerciale — Baja California Sur")

st.write(
    "Répertorie tes prospects, évalue leur potentiel "
    "et organise tes visites commerciales."
)

if "prospects" not in st.session_state:
    st.session_state.prospects = []

st.header("Ajouter un établissement")

with st.form("prospect_form"):
    nom = st.text_input("Nom de l'établissement")
    ville = st.selectbox(
        "Ville",
        [
            "La Paz",
            "Todos Santos",
            "Cabo San Lucas",
            "San José del Cabo",
            "Autre"
        ]
    )
    categorie = st.selectbox(
        "Type d'établissement",
        [
            "Restaurant gastronomique",
            "Restaurant",
            "Hôtel de luxe",
            "Hôtel boutique",
            "Bar à vin",
            "Caviste",
            "Distributeur",
            "Autre"
        ]
    )
    potentiel = st.slider(
        "Potentiel commercial estimé",
        0, 100, 50
    )
    contact = st.text_input("Contact ou responsable")
    telephone = st.text_input("Téléphone")
    notes = st.text_area("Notes commerciales")

    valide = st.form_submit_button("Ajouter le prospect")

    if valide:
        if nom.strip():
            st.session_state.prospects.append({
                "Nom": nom.strip(),
                "Ville": ville,
                "Type": categorie,
                "Score": potentiel,
                "Contact": contact,
                "Téléphone": telephone,
                "Notes": notes,
                "Statut": "À contacter"
            })
            st.success(f"{nom} ajouté à la liste.")
        else:
            st.error("Entre le nom de l'établissement.")

st.header("Classement des prospects")

if st.session_state.prospects:
    classement = sorted(
        st.session_state.prospects,
        key=lambda p: p["Score"],
        reverse=True
    )

    st.dataframe(
        classement,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Exporter les prospects en CSV",
        data=__import__("pandas").DataFrame(
            classement
        ).to_csv(index=False).encode("utf-8-sig"),
        file_name="prospects_vins.csv",
        mime="text/csv"
    )
else:
    st.info(
        "Aucun prospect pour le moment. "
        "Ajoute ton premier établissement ci-dessus."
    )

st.caption(
    "Version 1 — Les données sont provisoires "
    "et ne sont pas encore sauvegardées dans une base permanente."
)
