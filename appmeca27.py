import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"
# Lien pour lire l'onglet 'Utilisateurs' (le premier par défaut)
URL_USERS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

st.set_page_config(page_title="Vote Classe", page_icon="🏫")

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=0) # Pas de cache pour avoir les modifs en temps réel
def load_data(url):
    return pd.read_csv(url)

try:
    df_users = load_data(URL_USERS)
except Exception as e:
    st.error("Impossible de lire le Google Sheet. Vérifie qu'il est bien partagé en 'Tous les utilisateurs disposant du lien' !")
    st.stop()

# --- LOGIN ---
if 'connecte' not in st.session_state:
    st.session_state.connecte = False

if not st.session_state.connecte:
    st.title("Connexion 🔒")
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + df_users["Nom"].tolist())
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        vrai_mdp = str(df_users[df_users["Nom"] == user_choisi]["password"].values[0])
        if str(mdp_saisi) == vrai_mdp:
            st.session_state.connecte = True
            st.session_state.user = user_choisi
            st.rerun()
        else:
            st.error("Mauvais mot de passe")

# --- VOTE ---
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    st.subheader("Question : Qui est le plus en retard ?")
    
    # Pour le vote, on reste sur un système de session pour l'instant 
    # car l'écriture (update) demande une configuration de clé API complexe.
    if 'votes_du_jour' not in st.session_state:
        st.session_state.votes_du_jour = []

    if st.session_state.user not in [v['votant'] for v in st.session_state.votes_du_jour]:
        cible = st.radio("Désigne le coupable :", df_users["Nom"].tolist())
        if st.button("Valider mon vote"):
            st.session_state.votes_du_jour.append({'votant': st.session_state.user, 'cible': cible})
            st.success("Vote pris en compte !")
            st.rerun()
    else:
        st.warning("Tu as déjà voté aujourd'hui !")
        
        # Affichage des résultats
        if st.session_state.votes_du_jour:
            df_v = pd.DataFrame(st.session_state.votes_du_jour)
            stats = df_v['cible'].value_counts(normalize=True) * 100
            for nom, pct in stats.items():
                st.write(f"**{nom}** : {int(pct)}%")
                st.progress(int(pct))

    if st.button("Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
