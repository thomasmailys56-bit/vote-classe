import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
# Remplace bien par TON ID de document entre les guillemets
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"

def get_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CHARGEMENT DES DONNÉES ---
try:
    # Lecture de l'onglet Utilisateurs
    df_users = pd.read_csv(get_url("Utilisateurs"))
    # Lecture de l'onglet Votes
    df_votes = pd.read_csv(get_url("Votes"))
    st.sidebar.success("✅ Connecté au Google Sheet")
except Exception as e:
    st.error("❌ Erreur de lecture du Google Sheet")
    st.info("Vérifie que tes onglets s'appellent exactement 'Utilisateurs' et 'Votes' et que le fichier est partagé en 'Tous les utilisateurs disposant du lien'.")
    st.stop()

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    # On nettoie les noms pour enlever les espaces vides
    liste_noms = df_users["Nom"].dropna().tolist()
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if user_choisi != "Choisir...":
            # On récupère le vrai mot de passe
            vrai_mdp = str(df_users[df_users["Nom"] == user_choisi]["password"].values[0])
            if str(mdp_saisi) == vrai_mdp:
                st.session_state.user = user_choisi
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
else:
    # --- INTERFACE DE VOTE ---
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # Vérifier si l'utilisateur a déjà voté
    deja_vote = False
    if not df_votes.empty and "Votant" in df_votes.columns:
        if st.session_state.user in df_votes["Votant"].astype(str).values:
            deja_vote = True

    if not deja_vote:
        st.subheader("Qui est le plus en retard ?")
        cible = st.radio("Désigne un élève :", liste_noms)
        
        if st.button("Valider mon vote"):
            st.success("Vote validé ! (Enregistrement en attente de configuration API)")
            # Note : L'écriture nécessite la clé JSON, on teste d'abord la lecture.
            st.balloons()
    else:
        st.warning("Tu as déjà voté !")
        if not df_votes.empty:
            st.write("### Résultats actuels")
            st.bar_chart(df_votes["Cible"].value_counts())

    if st.button("Déconnexion"):
        del st.session_state.user
        st.rerun()
