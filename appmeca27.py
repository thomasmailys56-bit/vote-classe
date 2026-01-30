import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Vote Classe", page_icon="🏫")

# --- LE MOTEUR (À METTRE ICI) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Lit le premier onglet (Utilisateurs)
    df_users = conn.read(ttl=0).dropna(how="all")
    
    # Lit le deuxième onglet (Votes)
    # Si l'onglet s'appelle bien "Votes", ça marchera
    df_votes = conn.read(worksheet="Votes", ttl=0)
    st.sidebar.success("Connexion Sheets OK !")
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.info("Vérifie l'URL dans les Secrets et les noms d'onglets (Utilisateurs et Votes)")
    st.stop() # On arrête tout si la connexion échoue

# --- CONNEXION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 1. Test lecture Utilisateurs
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    st.sidebar.success("✅ Onglet 'Utilisateurs' lu !")
    
    # 2. Test lecture ou création Votes
    try:
        df_votes = conn.read(worksheet="Votes", ttl=0)
        st.sidebar.success("✅ Onglet 'Votes' lu !")
    except:
        st.sidebar.warning("⚠️ Onglet 'Votes' introuvable ou vide.")
        df_votes = pd.DataFrame(columns=["Votant", "Cible"])

except Exception as e:
    st.error(f"❌ Erreur de connexion fatale : {e}")
    st.info("Vérifie que ton lien dans 'Secrets' est correct et que le Sheet est en 'Tous les utilisateurs disposant du lien : ÉDITEUR'")
    st.stop()

# --- INTERFACE DE LOGIN ---
if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    nom = st.selectbox("Ton nom", ["Choisir..."] + df_users["Nom"].tolist())
    mdp = st.text_input("Mot de passe", type="password")
    
    if st.button("Entrer"):
        row = df_users[df_users["Nom"] == nom]
        if not row.empty and str(row["password"].values[0]) == mdp:
            st.session_state.user = nom
            st.rerun()
        else:
            st.error("Identifiants incorrects")

# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.user} !")
    
    # On vérifie si l'utilisateur a déjà voté
    a_vote = False
    if not df_votes.empty and "Votant" in df_votes.columns:
        if st.session_state.user in df_votes["Votant"].astype(str).values:
            a_vote = True

    if not a_vote:
        cible = st.radio("Qui est le plus en retard ?", df_users["Nom"].tolist())
        if st.button("Voter"):
            try:
                # Créer le nouveau vote
                nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                maj = pd.concat([df_votes, nouveau], ignore_index=True)
                
                # ESSAI D'ECRITURE
                conn.update(worksheet="Votes", data=maj)
                st.success("Vote enregistré !")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Impossible d'écrire le vote : {e}")
                st.info("C'est ici que ça bloque : Google refuse l'écriture sans clé JSON 'Service Account'.")
    else:
        st.info("Tu as déjà voté. Voici les scores :")
        st.write(df_votes["Cible"].value_counts())

    if st.button("Sortir"):
        del st.session_state.user
        st.rerun()
