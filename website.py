import streamlit as st
from categories_update_page import app as cat_updater
import pandas as pd
import numpy as np
import hmac
from functions import *

st.set_page_config(layout="wide")

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

#@st.cache_data
def load_full_data():
    df = pd.read_csv("promos.csv")
    df["description de l'offre"] = df["description de l'offre en 1 phrase"]
    df = df[["marque", "description de l'offre","code", "lien", "dates"]]
    df.fillna("")
    return df

#@st.cache_data
def load_categories_dict():
    cat_dict = np.load("categorie_to_marque.npy", allow_pickle="TRUE")
    cat_dict = dict(enumerate(cat_dict.flatten(), 1))
    return cat_dict[1]

if "full_data" not in st.session_state:
    full_data = load_full_data()
    cat_dict = load_categories_dict()
    st.session_state["full_data"] = full_data
    st.session_state["cat_dict"] = cat_dict
    st.session_state["in_cat_update"] = False

st.title(":sparkles: code promotionnel :sparkles:")

st.sidebar.image("logo.png")
st.sidebar.write('Catégories:')
option_0 = st.sidebar.checkbox("Tous", value=True)
option_1 = st.sidebar.checkbox("Mode")
option_2 = st.sidebar.checkbox("Technologie et gaming")
option_3 = st.sidebar.checkbox("Santé & cosmétique")
option_4 = st.sidebar.checkbox("Maison")
option_5 = st.sidebar.checkbox("Sport et loisirs")
option_6 = st.sidebar.checkbox("Automobile")
option_7 = st.sidebar.checkbox("Animaux")
option_8 = st.sidebar.checkbox("Nutrition")
option_9 = st.sidebar.checkbox("Finance")
st.sidebar.markdown("----------------------------")
st.sidebar.write("__Admninistrateur__")
if st.sidebar.button("update data"):
    if not check_password():
        st.stop()
    else:
        gpt_api_key = st.secrets["gpt_api_key"]
        youtube_api_key = st.secrets["youtube_key"]
        df_cd_promo = get_new_code_promo(gpt_api_key, youtube_api_key)
        old_df_cd_promo = pd.read_csv(f"{os.getcwd()}/promos.csv",index_col=False)
        if df_cd_promo.empty:
            new_df_cd_promo = old_df_cd_promo
        else:
            new_df_cd_promo = old_df_cd_promo.append(df_cd_promo,sort=False)
        new_df_cd_promo["reduction (time)"] = new_df_cd_promo["description de l'offre en 1 phrase"].apply(get_period_intensity)
        new_df_cd_promo = sort_promo(new_df_cd_promo)
        new_df_cd_promo.to_csv("promos.csv", index=False)
        git_password = st.secrets["git_password"]
        git_commit("promos.csv",git_password)
        git_commit("historical_urls.csv",git_password)
        new_df_cd_promo["description de l'offre"] = new_df_cd_promo["description de l'offre en 1 phrase"]
        new_df_cd_promo = new_df_cd_promo[["marque", "description de l'offre","code", "lien", "dates"]]
        st.sidebar.write("updated!")
        st.session_state["full_data"] = new_df_cd_promo

if st.sidebar.button("clean data"):
    if not check_password():
        st.stop()
    else:
        clean_historical_urls(dt.datetime.combine(dt.date.today() - dt.timedelta(days=50), dt.datetime.min.time()))
        clean_promos(dt.datetime.combine(dt.date.today() - dt.timedelta(days=50), dt.datetime.min.time()))
        git_password = st.secrets["git_password"]
        git_commit("promos.csv",git_password)
        git_commit("historical_urls.csv",git_password)
        st.sidebar.write("cleaned & commited!")

if (st.sidebar.button("update categories")) or st.session_state["in_cat_update"]:
    if not check_password():
        st.stop()
    else:
        st.session_state["in_cat_update"] = True
        cat_updater()
        git_password = st.secrets["git_password"]
        git_commit("categorie_to_marque.npy",git_password)
        st.sidebar.write("categories updated!")
st.sidebar.markdown("----------------------------")          
selected_rows = []
for index,row in st.session_state["full_data"].iterrows():
    selected_tamp = False
    if option_0:
        selected_tamp = True
    if (option_1) and (row["marque"] in st.session_state["cat_dict"]["mode"]):
        selected_tamp = True
    if (option_2) and (row["marque"] in st.session_state["cat_dict"]["technologie et gaming"]):
        selected_tamp = True
    if (option_3) and (row["marque"] in st.session_state["cat_dict"]["santé & cosmétique"]):
        selected_tamp = True
    if (option_4) and (row["marque"] in st.session_state["cat_dict"]["maison"]):
        selected_tamp = True
    if (option_5) and (row["marque"] in st.session_state["cat_dict"]["sport et loisirs"]):
        selected_tamp = True
    if (option_6) and (row["marque"] in st.session_state["cat_dict"]["automobile"]):
        selected_tamp = True
    if (option_7) and (row["marque"] in st.session_state["cat_dict"]["animaux"]):
        selected_tamp = True
    if (option_8) and (row["marque"] in st.session_state["cat_dict"]["nutrition"]):
        selected_tamp = True
    if (option_9) and (row["marque"] in st.session_state["cat_dict"]["finance"]):
        selected_tamp = True
    selected_rows.append(selected_tamp)
data = st.session_state["full_data"][selected_rows]
st.dataframe(
    data,
    hide_index=True,
    width=5000,
    height=700,
    column_config={
        "lien": st.column_config.LinkColumn("lien"),
    },
    background-color="gray"
)
