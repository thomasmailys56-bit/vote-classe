import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Créer la connexion au Google Sheet
# Tu devras mettre l'URL de ton Google Sheet dans les secrets de Streamlit après
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Lire les données des élèves
# On imagine que ton onglet s'appelle "Utilisateurs"
df_eleves = conn.read(worksheet="Utilisateurs")
liste_eleves = df_eleves["Nom"].tolist() # Récupère la colonne "Nom"

st.title("Vote pour la classe")

# 3. Utiliser la vraie liste dans le menu
choix = st.selectbox("Qui es-tu ?", liste_eleves)


# --- INTERFACE DE VOTE ---
else:
    st.title(f"Salut {st.session_state.user_actuel} ! 👋")
    question = "Qui est le plus en retard ?"
    eleves = ["Lucas", "Emma", "Nathan", "Jade"]

    # Vérifier si l'utilisateur a déjà voté
    deja_vote = st.session_state.votes_db[st.session_state.votes_db['votant'] == st.session_state.user_actuel]

    if deja_vote.empty:
        st.subheader(question)
        for eleve in eleves:
            if st.button(f"Voter pour {eleve}"):
                nouveau_vote = pd.DataFrame([{'votant': st.session_state.user_actuel, 'cible': eleve}])
                st.session_state.votes_db = pd.concat([st.session_state.votes_db, nouveau_vote], ignore_index=True)
                st.success("Vote enregistré !")
                st.rerun()
    else:
        st.warning("Tu as déjà voté ! Voici les résultats :")
        # Calcul des %
        stats = st.session_state.votes_db['cible'].value_counts(normalize=True) * 100
        for nom, pct in stats.items():
            st.write(f"**{nom}** ({int(pct)}%)")
            st.progress(int(pct))
            
    if st.button("Déconnexion"):
        st.session_state.logged_in = False
        st.rerun()
