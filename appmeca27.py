import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="App de la Classe", page_icon="🔒")

# Simulation de base de données (À connecter plus tard au Sheets)
if 'users' not in st.session_state:
    st.session_state.users = {"admin": "123", "lucas": "pass", "emma": "abc"}
if 'votes_db' not in st.session_state:
    st.session_state.votes_db = pd.DataFrame(columns=['votant', 'cible'])
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- ECRAN DE CONNEXION ---
if not st.session_state.logged_in:
    st.title("Connexion 🏫")
    user = st.text_input("Nom d'utilisateur").lower()
    pw = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        if user in st.session_state.users and st.session_state.users[user] == pw:
            st.session_state.logged_in = True
            st.session_state.user_actuel = user
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    
    st.info("Note : Pour l'instant, utilise lucas/pass ou emma/abc")

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
