import streamlit as st
from functions import *

def app():
    categories = ["mode", "technologie et gaming", "santé & cosmétique", "maison", "sport et loisirs", "automobile", "animaux", "nutrition", "finance", "autre"]
    selected_options = {}
    marques = list(st.session_state["full_data"]["marque"].unique())
    new_marques = []
    for mark in marques:
        if mark not in np.sum([st.session_state["cat_dict"][cat] for cat in st.session_state["cat_dict"]]):
            new_marques.append(mark)
    i = 0
    for mark in new_marques:
        col1, col2 = st.columns(2)
        with col1:
            st.write(mark)
        with col2:
            selected_options[mark] = st.multiselect(
                "Sélectionnez une ou plusieurs catégories",
                [f"{cat} + {i}" for cat in categories],
            )
        i += 1
    if st.button("cliquez pour valider vos choix"):
        for mark in selected_options:
            for cat in selected_options[mark]:
                if cat.split(" + ")[0] != "autre":
                    st.session_state["cat_dict"][cat.split(" + ")[0]].append(mark)
        st.session_state["in_cat_update"] = False
        np.save("categorie_to_marque.npy", st.session_state["cat_dict"])
