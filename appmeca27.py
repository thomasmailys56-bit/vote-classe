import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random  # <--- AJOUTÉ pour le tirage au sort

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CONNEXION SÉCURISÉE ---
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lecture des 3 onglets
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    df_votes = conn.read(worksheet="Votes", ttl=0)
    
    # Sécurité pour l'onglet Question
    try:
        df_q = conn.read(worksheet="Question", ttl=0)
        if not df_q.empty:
            question_actuelle = df_q.iloc[-1]["Texte"]
        else:
            question_actuelle = "Pas encore de question !"
    except:
        question_actuelle = "Qui est le plus en retard ?"
        df_q = pd.DataFrame(columns=["Texte", "Date", "Auteur"])

    liste_noms = df_users["Nom"].dropna().unique().tolist()
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- TIRAGE DE L'ADMIN DU JOUR (Fixe pour 24h) ---
date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
# On utilise la date comme "graine" pour que le choix soit le même pour tout le monde
random.seed(int(datetime.now().strftime("%Y%m%d")))
if liste_noms:
    admin_du_jour = random.choice(liste_noms)
else:
    admin_du_jour = "Aucun"

# --- LOGIN ---
if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
    mdp_saisi = st.text_input("Mot de passe", type="password", key="login_mdp")

    if st.button("Se connecter", key="login_btn"):
        vrai_mdp = str(df_users[df_users["Nom"] == user_choisi]["password"].values[0])
        if str(mdp_saisi) == vrai_mdp:
            st.session_state.user = user_choisi
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
else:
    # --- INTERFACE UTILISATEUR ---
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # AFFICHAGE DE LA QUESTION DU JOUR
    st.info(f"✨ **Question :** {question_actuelle}")
    
    # Vérifier si déjà voté
    a_vote = st.session_state.user in df_votes["Votant"].astype(str).values

    if not a_vote:
        cible = st.radio("Fais ton choix :", liste_noms, key="radio_vote")
        if st.button("Valider mon vote", key="btn_vote"):
            nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
            maj = pd.concat([df_votes, nouveau], ignore_index=True)
            conn.update(worksheet="Votes", data=maj)
            st.success("Vote enregistré !")
            st.balloons()
            st.rerun()
    else:
        st.warning("Tu as déjà voté !")
        if not df_votes.empty:
            st.write("### Résultats")
            st.bar_chart(df_votes["Cible"].value_counts())

    # --- SECTION ADMIN ALÉATOIRE ---
    st.divider()
    st.write(f"👑 L'administrateur du jour est : **{admin_du_jour}**")
    
    # Vérifier si une question a déjà été postée AUJOURD'HUI
    deja_fait_aujourdhui = False
    if not df_q.empty:
        if date_aujourdhui in df_q["Date"].astype(str).values:
            deja_fait_aujourdhui = True

    # Seul l'admin du jour voit le menu, et seulement s'il n'a pas encore changé la question
    if st.session_state.user == admin_du_jour:
        if not deja_fait_aujourdhui:
            with st.expander("⚙️ Modifier la question (Ton tour !)"):
                st.write("Tu ne peux changer la question qu'une seule fois par jour.")
                nouvelle_q = st.text_input("Nouvelle question pour demain :", key="input_admin")
                
                if st.button("Mettre à jour la question", key="btn_admin"):
                    if nouvelle_q:
                        # 1. On ajoute la nouvelle question à l'historique
                        df_nouvelle_q = pd.DataFrame([{
                            "Texte": nouvelle_q, 
                            "Date": date_aujourdhui,
                            "Auteur": st.session_state.user
                        }])
                        df_q_maj = pd.concat([df_q, df_nouvelle_q], ignore_index=True)
                        conn.update(worksheet="Question", data=df_q_maj)
                        
                        # 2. On vide l'onglet Votes
                        df_vide = pd.DataFrame(columns=["Votant", "Cible"])
                        conn.update(worksheet="Votes", data=df_vide)
                        
                        st.success("C'est fait ! La question est enregistrée.")
                        st.rerun()
                    else:
                        st.error("Écris quelque chose !")
        else:
            st.success("✅ La question du jour a déjà été validée.")
    else:
        st.write("🔒 Tu n'es pas l'administrateur aujourd'hui.")

    if st.button("Déconnexion", key="btn_logout"):
        del st.session_state.user
        st.rerun()
