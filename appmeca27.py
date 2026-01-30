import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random

st.set_page_config(page_title="Vote & Chat Classe", page_icon="💬")

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lecture des 4 onglets
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    df_votes = conn.read(worksheet="Votes", ttl=0)
    df_q = conn.read(worksheet="Question", ttl=0)
    # Lecture du nouvel onglet Messages
    try:
        df_chat = conn.read(worksheet="Messages", ttl=0)
    except:
        df_chat = pd.DataFrame(columns=["Utilisateur", "Message", "Heure"])

    liste_noms = df_users["Nom"].dropna().unique().tolist()
    
    # Question actuelle
    if not df_q.empty:
        question_actuelle = df_q.iloc[-1]["Texte"]
    else:
        question_actuelle = "Pas encore de question !"

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- ADMIN DU JOUR ---
date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
random.seed(int(datetime.now().strftime("%Y%m%d")))
admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"

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
    # --- INTERFACE ---
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    # ONGLES Streamlit pour séparer Vote et Chat
    tab1, tab2 = st.tabs(["🗳️ Vote", "💬 Discussion"])

    with tab1:
        st.info(f"✨ **Question :** {question_actuelle}")
        a_vote = st.session_state.user in df_votes["Votant"].astype(str).values

        if not a_vote:
            cible = st.radio("Fais ton choix :", liste_noms, key="radio_vote")
            if st.button("Valider mon vote", key="btn_vote"):
                nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                maj = pd.concat([df_votes, nouveau], ignore_index=True)
                conn.update(worksheet="Votes", data=maj)
                st.success("Vote enregistré !")
                st.rerun()
        else:
            st.warning("Tu as déjà voté !")
            if not df_votes.empty:
                st.bar_chart(df_votes["Cible"].value_counts())

    with tab2:
        st.subheader("Mur de la classe")
        
        # Formulaire d'envoi
        with st.form("chat_form", clear_on_submit=True):
            msg_texte = st.text_input("Ton message :")
            submit = st.form_submit_button("Envoyer")
            
            if submit and msg_texte:
                nouveau_msg = pd.DataFrame([{
                    "Utilisateur": st.session_state.user,
                    "Message": msg_texte,
                    "Heure": datetime.now().strftime("%H:%M")
                }])
                df_chat_maj = pd.concat([df_chat, nouveau_msg], ignore_index=True)
                conn.update(worksheet="Messages", data=df_chat_maj)
                st.rerun()

        # Affichage des messages (du plus récent au plus ancien)
        st.divider()
        if not df_chat.empty:
            # On inverse pour voir les derniers en haut
            for i, row in df_chat.iloc[::-1].head(20).iterrows():
                with st.chat_message("user" if row['Utilisateur'] != st.session_state.user else "assistant"):
                    st.write(f"**{row['Utilisateur']}** ({row['Heure']})")
                    st.write(row['Message'])
        else:
            st.write("Aucun message pour le moment.")

    # --- ADMIN ---
    st.divider()
    st.write(f"👑 Admin du jour : **{admin_du_jour}**")
    if st.session_state.user == admin_du_jour:
        deja_fait = not df_q.empty and date_aujourdhui in df_q["Date"].astype(str).values
        if not deja_fait:
            with st.expander("⚙️ Modifier la question"):
                nouvelle_q = st.text_input("Nouvelle question :", key="in_admin")
                if st.button("Mettre à jour", key="bt_admin"):
                    df_nouvelle_q = pd.DataFrame([{"Texte": nouvelle_q, "Date": date_aujourdhui, "Auteur": st.session_state.user}])
                    conn.update(worksheet="Question", data=pd.concat([df_q, df_nouvelle_q], ignore_index=True))
                    conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                    st.rerun()

    if st.button("Déconnexion", key="btn_logout"):
        del st.session_state.user
        st.rerun()
