import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuration de la page
st.set_page_config(page_title="Le Dossier de la Classe", page_icon="🏫")

st.title("🗳️ Le Vote du Jour")

# 2. Simulation de base de données (À remplacer par un vrai fichier plus tard)
if 'votes' not in st.session_state:
    st.session_state.votes = pd.DataFrame(columns=['Question', 'Votant', 'Cible'])

eleves = ["Lucas", "Emma", "Nathan", "Jade", "Léo", "Chloé"]
question_du_jour = "Qui est le plus susceptible de s'endormir en cours ?"

# 3. Interface principale
st.subheader(f"Question : {question_du_jour}")

# Sélection de l'élève qui vote (pour le test)
moi = st.selectbox("Qui es-tu ?", eleves)

st.write("Désigne une personne :")

# Création des boutons pour chaque élève
cols = st.columns(3)
for i, eleve in enumerate(eleves):
    with cols[i % 3]:
        if st.button(eleve, key=eleve):
            # Enregistrement du vote
            nouveau_vote = {'Question': question_du_jour, 'Votant': moi, 'Cible': eleve}
            st.session_state.votes = st.session_state.votes.append(nouveau_vote, ignore_index=True)
            st.success(f"A voté pour {eleve} !")

# 4. Affichage des résultats en pourcentage
st.divider()
st.subheader("📊 Résultats actuels")

if not st.session_state.votes.empty:
    stats = st.session_state.votes['Cible'].value_counts(normalize=True) * 100
    for nom, pct in stats.items():
        st.write(f"**{nom}**")
        st.progress(int(pct))
        st.caption(f"{int(pct)}%")
else:
    st.info("Aucun vote pour le moment.")
