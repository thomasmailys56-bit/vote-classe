import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CONNEXION ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    df_votes = conn.read(worksheet="Votes", ttl=0)
    # On lit la question actuelle
    df_q = conn.read(worksheet="Question", ttl=0)
    
    liste_noms = df_users["Nom"].dropna().unique().tolist()
    
    # Récupérer la dernière question posée
    if not df_q.empty:
        question_actuelle = df_q.iloc[-1]["Texte"]
        date_question = df_q.iloc[-1]["Date"]
    else:
        question_actuelle = "Pas encore de question !"
        date_question = ""
        
except Exception as e:
    st.error("Erreur de connexion. Vérifie les Secrets !")
    st.stop()

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
    mdp_saisi = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        vrai_mdp = str(df_users[df_users["Nom"] == user_choisi]["password"].values[0])
        if str(mdp_saisi) == vrai_mdp:
            st.session_state.user = user_choisi
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
else:
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # --- AFFICHAGE DE LA QUESTION ---
    st.info(f"✨ **Question du jour :** {question_actuelle}")
    
    # Vérifier si déjà voté
    a_vote = st.session_state.user in df_votes["Votant"].astype(str).values

    if not a_vote:
        cible = st.radio("Fais ton choix :", liste_noms)
        if st.button("Valider mon vote"):
            nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
            maj = pd.concat([df_votes, nouveau], ignore_index=True)
            conn.update(worksheet="Votes", data=maj)
            st.success("Vote enregistré !")
            st.rerun()
    else:
        st.warning("Tu as déjà voté !")
        if not df_votes.empty:
            st.bar_chart(df_votes["Cible"].value_counts())

    # --- SECTION ADMIN : CHOISIR LA PROCHAINE QUESTION ---
    st.divider()
    with st.expander("⚙️ Proposer la question de demain"):
        st.write("Attention : cela effacera aussi les votes actuels pour recommencer à zéro.")
        nouvelle_q = st.text_input("Quelle est la prochaine question ?")
        
        if st.button("Mettre à jour la question"):
            if nouvelle_q:
                # 1. Enregistrer la nouvelle question
                df_nouvelle_q = pd.DataFrame([{
                    "Texte": nouvelle_q, 
                    "Date": datetime.now().strftime("%d/%m/%Y"),
                    "Auteur": st.session_state.user
                }])
                conn.update(worksheet="Question", data=df_nouvelle_q)
                
                # 2. Réinitialiser les votes (Vider l'onglet Votes)
                df_vide = pd.DataFrame(columns=["Votant", "Cible"])
                conn.update(worksheet="Votes", data=df_vide)
                
                st.success("La question a été changée et les votes réinitialisés !")
                st.rerun()
            else:
                st.error("Écris une question d'abord !")

    if st.button("Déconnexion"):
        del st.session_state.user
        st.rerun()
