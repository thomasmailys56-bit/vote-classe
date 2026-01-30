import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CONNEXION AU GOOGLE SHEET ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # On lit l'onglet "Utilisateurs"
    df_eleves = conn.read(worksheet="Utilisateurs")
    liste_eleves = df_eleves["Nom"].tolist()
except Exception as e:
    st.error("Erreur de connexion au Sheet. Vérifie tes 'Secrets' !")
    st.stop()

# --- INITIALISATION ---
if 'votes' not in st.session_state:
    st.session_state.votes = pd.DataFrame(columns=['Votant', 'Cible'])

st.title("🏫 Le Vote de la Classe")

# --- INTERFACE ---
# On utilise la vraie liste venant du Google Sheet !
moi = st.selectbox("Qui es-tu ?", ["Sélectionne ton nom"] + liste_eleves)

if moi != "Sélectionne ton nom":
    st.subheader("Qui est le plus en retard ?")
    
    # On affiche les boutons pour chaque élève de la liste
    cols = st.columns(2)
    for i, eleve in enumerate(liste_eleves):
        with cols[i % 2]:
            if st.button(f"Voter pour {eleve}", key=eleve):
                # On enregistre le vote
                nouveau_vote = pd.DataFrame([{'Votant': moi, 'Cible': eleve}])
                st.session_state.votes = pd.concat([st.session_state.votes, nouveau_vote], ignore_index=True)
                st.success(f"Merci ! Vote pour {eleve} enregistré.")

    # --- RESULTATS ---
    st.divider()
    if not st.session_state.votes.empty:
        st.write("### 📊 Résultats")
        stats = st.session_state.votes['Cible'].value_counts(normalize=True) * 100
        for nom, pct in stats.items():
            st.write(f"**{nom}** : {int(pct)}%")
            st.progress(int(pct))
