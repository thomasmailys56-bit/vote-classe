import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import random
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Meca 27", page_icon="🗳️")

# --- CONNEXION ---
# L'ID de ton sheet
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"

def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = load_data("Utilisateurs")
    df_votes = load_data("Votes")
    df_q = load_data("Question")
    
    # Sécurité pour le chat
    try:
        df_chat = load_data("Messages")
    except:
        df_chat = pd.DataFrame(columns=["Utilisateur", "Message", "Heure"])

    liste_noms = df_users["Nom"].dropna().unique().tolist()
    
    # Question du jour
    date_auj = datetime.now().strftime("%d/%m/%Y")
    q_row = df_q[df_q["Date"].astype(str) == date_auj]
    question = q_row.iloc[-1]["Texte"] if not q_row.empty else "Pas de question aujourd'hui ! 😴"

except Exception as e:
    st.error(f"Erreur de lecture du Sheet. Vérifie les noms d'onglets ! ({e})")
    st.stop()

# --- AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.title("🏢 Meca 27 • Connexion")
    mode = st.radio("Option :", ["Connexion", "Inscription"], horizontal=True)
    
    with st.container(border=True):
        if mode == "Connexion":
            u_sel = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
            p_sel = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                user_row = df_users[df_users["Nom"] == u_sel]
                if not user_row.empty and str(p_sel) == str(user_row["password"].values[0]):
                    st.session_state.user = u_sel
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        else:
            n_nom = st.text_input("Ton Nom / Surnom")
            n_mdp = st.text_input("Mot de passe", type="password")
            if st.button("Créer mon compte"):
                if n_nom and n_mdp and n_nom not in liste_noms:
                    new_user = pd.DataFrame([{"Nom": n_nom, "password": n_mdp}])
                    conn.update(worksheet="Utilisateurs", data=pd.concat([df_users, new_user], ignore_index=True))
                    st.session_state.user = n_nom
                    st.cache_data.clear()
                    st.rerun()
                else: st.error("Nom invalide ou déjà pris.")

else:
    # --- INTERFACE CONNECTÉE ---
    st.write(f"Connecté : **{st.session_state.user}**")
    
    # Temps restant
    demain = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    diff = demain - datetime.now()
    st.caption(f"⏳ Fin du vote dans : {diff.seconds // 3600}h {(diff.seconds // 60) % 60}min")

    tab1, tab2 = st.tabs(["🗳️ Vote", "💬 Chat"])

    with tab1:
        st.subheader(question)
        deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values if not df_votes.empty else False

        if not deja_vote and "Pas de question" not in question:
            choix = st.radio("Désigne ta cible :", liste_noms, horizontal=True)
            if st.button("Valider le vote"):
                nv_v = pd.DataFrame([{"Votant": st.session_state.user, "Cible": choix}])
                conn.update(worksheet="Votes", data=pd.concat([df_votes, nv_v], ignore_index=True))
                st.rerun()
        else:
            if not df_votes.empty:
                res = df_votes["Cible"].value_counts().reset_index()
                res.columns = ["Nom", "Votes"]
                fig = px.bar(res, x="Votes", y="Nom", orientation='h', text="Votes")
                fig.update_layout(xaxis={'visible': False}, yaxis={'title': ''}, height=300)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        # Chat simplifié
        chat_zone = st.container(height=300)
        with chat_zone:
            for _, row in df_chat.iloc[::-1].iterrows():
                st.markdown(f"**{row['Utilisateur']}** : {row['Message']}")
        
        with st.form("msg", clear_on_submit=True):
            m = st.text_input("Ton message...")
            if st.form_submit_button("Envoyer") and m:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": m, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- ADMIN & DÉCONNEXION ---
    st.divider()
    if st.button("Déconnexion 🚪"):
        del st.session_state.user
        st.rerun()
