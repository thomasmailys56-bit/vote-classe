import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des élèves (sans cache pour avoir les nouveaux noms direct)
df_users = conn.read(worksheet="Utilisateurs", ttl=0).dropna(how="all")

# --- LOGIQUE DE CONNEXION ---
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

# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # 1. Charger les votes actuels pour vérifier si l'user a déjà voté
    df_votes = conn.read(worksheet="Votes", ttl=0).dropna(how="all")
    
    # Vérification : est-ce que mon nom est déjà dans la colonne 'Votant' ?
    deja_vote = st.session_state.user in df_votes["Votant"].values

    if not deja_vote:
        st.subheader("Question du jour : Qui est le plus en retard ?")
        cible = st.radio("Désigne le coupable :", df_users["Nom"].tolist())
        
        if st.button("Valider mon vote"):
            # Préparation de la nouvelle ligne
            nouveau_vote = pd.DataFrame([{
                "Votant": st.session_state.user,
                "Cible": cible,
                "Date": datetime.now().strftime("%d/%m/%Y")
            }])
            
            # AJOUT AU GOOGLE SHEET
            df_maj = pd.concat([df_votes, nouveau_vote], ignore_index=True)
            conn.update(worksheet="Votes", data=df_maj)
            
            st.success("Vote enregistré !")
            st.balloons()
            st.rerun()
    else:
        st.warning("Tu as déjà voté ! Voici les résultats :")
        
        # Calcul des pourcentages en temps réel
        if not df_votes.empty:
            stats = df_votes["Cible"].value_counts(normalize=True) * 100
            for nom, pct in stats.items():
                st.write(f"**{nom}** : {int(pct)}%")
                st.progress(int(pct))

    # --- BOUTON RESET (Seulement pour toi / Admin) ---
    st.divider()
    if st.session_state.user == "Lucas": # Change par ton nom
        if st.button("🗑️ Réinitialiser les votes (Nouvelle question)"):
            # On crée un tableau vide avec juste les colonnes
            df_vide = pd.DataFrame(columns=["Votant", "Cible", "Date"])
            conn.update(worksheet="Votes", data=df_vide)
            st.success("Votes réinitialisés !")
            st.rerun()

    if st.button("Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
