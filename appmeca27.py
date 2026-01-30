import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    df_votes = conn.read(worksheet="Votes", ttl=0)
    df_q = conn.read(worksheet="Question", ttl=0)
    
    liste_noms = df_users["Nom"].dropna().unique().tolist()
    
    # On récupère la toute dernière question enregistrée
    if not df_q.empty:
        # .iloc[-1] permet de prendre la dernière ligne du tableau
        question_actuelle = df_q.iloc[-1]["Texte"]
    else:
        question_actuelle = "Pas encore de question !"
        
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter", key="btn_login"):
        vrai_mdp = str(df_users[df_users["Nom"] == user_choisi]["password"].values[0])
        if str(mdp_saisi) == vrai_mdp:
            st.session_state.user = user_choisi
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    st.info(f"✨ **Question du jour :** {question_actuelle}")
    
    a_vote = st.session_state.user in df_votes["Votant"].astype(str).values

    if not a_vote:
        cible = st.radio("Fais ton choix :", liste_noms)
        if st.button("Valider mon vote", key="btn_voter"):
            nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
            maj = pd.concat([df_votes, nouveau], ignore_index=True)
            conn.update(worksheet="Votes", data=maj)
            st.success("Vote enregistré !")
            st.rerun()
    else:
        st.warning("Tu as déjà voté !")
        if not df_votes.empty:
            st.bar_chart(df_votes["Cible"].value_counts())

    st.divider()
    
    # SECTION ADMIN
    with st.expander("⚙️ Proposer la question de demain"):
        nouvelle_q = st.text_input("Quelle est la prochaine question ?")
        if st.button("Mettre à jour la question", key="btn_admin_q"):
            if nouvelle_q:
                # Ajout de la question
                df_nouvelle_q = pd.DataFrame([{
                    "Texte": nouvelle_q, 
                    "Date": datetime.now().strftime("%d/%m/%Y"),
                    "Auteur": st.session_state.user
                }])
                # On concatène avec l'ancien historique des questions
                df_q_maj = pd.concat([df_q, df_nouvelle_q], ignore_index=True)
                conn.update(worksheet="Question", data=df_q_maj)
                
                # Reset des votes
                df_vide = pd.DataFrame(columns=["Votant", "Cible"])
                conn.update(worksheet="Votes", data=df_vide)
                
                st.success("Question changée !")
                st.rerun()

    if st.button("Déconnexion", key="btn_logout"):
        del st.session_state.user
        st.rerun()
