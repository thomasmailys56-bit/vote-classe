import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="App de Classe Sécurisée", page_icon="🔒")

# --- CONNEXION AU SHEET ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # On lit le Sheet (il doit y avoir les colonnes 'Nom' et 'Mot de passe')
    df_users = conn.read()
except Exception as e:
    st.error("Erreur de connexion au Sheet.")
    st.stop()

# --- GESTION DE LA CONNEXION ---
if 'connecte' not in st.session_state:
    st.session_state.connecte = False

if not st.session_state.connecte:
    st.title("Connexion 🏫")
    
    nom_saisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + df_users["Nom"].tolist())
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        # On vérifie si le mot de passe correspond au nom dans le Sheet
        mdp_correct = df_users[df_users["Nom"] == nom_saisi]["Mot de passe"].values[0]
        
        if str(mdp_saisi) == str(mdp_correct):
            st.session_state.connecte = True
            st.session_state.utilisateur = nom_saisi
            st.rerun()
        else:
            st.error("Mot de passe incorrect !")

# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.utilisateur} ! 👋")
    
    st.subheader("Question : Qui est le plus en retard ?")
    
    # Liste de tous les élèves pour voter
    choix_vote = st.radio("Désigne une personne :", df_users["Nom"].tolist())
    
    if st.button("Valider mon vote"):
        st.success(f"Tu as voté pour {choix_vote} !")
        # Ici on pourra ajouter l'enregistrement du vote dans le Sheet plus tard
        
    if st.button("Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
