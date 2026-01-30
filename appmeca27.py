import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Vote Classe Pro", page_icon="🏫")

# --- CONNEXION ---
# On utilise GSheetsConnection pour pouvoir ÉCRIRE
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CHARGEMENT DES DONNÉES (Rapide grâce au cache de 60s) ---
df_users = conn.read(worksheet="Utilisateurs", ttl=60)
# On essaie de lire l'onglet Votes, s'il n'existe pas on le crée
try:
    df_votes = conn.read(worksheet="Votes", ttl=0) # Les votes doivent être frais (ttl=0)
except:
    df_votes = pd.DataFrame(columns=["Votant", "Cible"])

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

# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # VERIFICATION SI DÉJÀ VOTÉ DANS LE SHEET
    a_deja_vote = False
    if not df_votes.empty:
        if st.session_state.user in df_votes["Votant"].values:
            a_deja_vote = True

    if not a_deja_vote:
        st.subheader("Qui est le plus en retard ?")
        cible = st.radio("Désigne le coupable :", df_users["Nom"].tolist())
        
        if st.button("Confirmer mon vote"):
            # Création de la nouvelle ligne de vote
            nouveau_vote = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
            
            # Mise à jour du Sheet (C'est ça qui rend le vote permanent !)
            df_final = pd.concat([df_votes, nouveau_vote], ignore_index=True)
            conn.update(worksheet="Votes", data=df_final)
            
            st.success("Vote enregistré dans le Google Sheet !")
            st.balloons()
            st.rerun()
    else:
        st.warning("Tu as déjà voté ! Voici les résultats de la classe :")
        if not df_votes.empty:
            stats = df_votes["Cible"].value_counts(normalize=True) * 100
            for nom, pct in stats.items():
                st.write(f"**{nom}** : {int(pct)}%")
                st.progress(int(pct))
        
    if st.button("Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
