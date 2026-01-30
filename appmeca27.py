import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="App de Classe", page_icon="🏫")

# --- CONNEXION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read().dropna(how="all") # On enlève les lignes vides
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- INITIALISATION ---
if 'connecte' not in st.session_state:
    st.session_state.connecte = False

# --- LOGIQUE DE CONNEXION ---
if not st.session_state.connecte:
    st.title("Connexion 🔒")
    
    # On récupère la liste des noms depuis la colonne "Nom"
    noms_disponibles = df["Nom"].tolist()
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + noms_disponibles)
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if user_choisi != "Choisir...":
            # On cherche le mot de passe dans la colonne "password"
            vrai_mdp = str(df[df["Nom"] == user_choisi]["password"].values[0])
            
            if str(mdp_saisi) == vrai_mdp:
                st.session_state.connecte = True
                st.session_state.user = user_choisi
                st.rerun()
            else:
                st.error("Mauvais mot de passe !")
        else:
            st.warning("Sélectionne ton nom d'abord.")

# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    st.subheader("Question : Qui est le plus en retard ?")
    
    # Liste pour voter (on peut voter pour n'importe qui dans la colonne Nom)
    cible = st.radio("Désigne le coupable :", df["Nom"].tolist())
    
    if st.button("Valider mon vote"):
        st.balloons()
        st.success(f"Ton vote contre {cible} a été enregistré (localement) !")
        
    if st.button("Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
