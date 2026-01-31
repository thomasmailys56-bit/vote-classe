import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Meca 27 - Vote", page_icon="🗳️")

# CSS Minimaliste pour éviter les conflits
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 15px; padding: 5px 15px; }
    [data-testid="stChatMessage"] { border-radius: 15px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNEXION DONNÉES ---
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"

def load_data(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = load_data("Utilisateurs")
    df_votes = load_data("Votes")
    df_q = load_data("Question")
    try:
        df_chat = load_data("Messages")
    except:
        df_chat = pd.DataFrame(columns=["Utilisateur", "Message", "Heure"])
    
    liste_noms = df_users["Nom"].dropna().unique().tolist()
    date_auj = datetime.now().strftime("%d/%m/%Y")
    q_row = df_q[df_q["Date"].astype(str) == date_auj]
    question_actuelle = q_row.iloc[-1]["Texte"] if not q_row.empty else "Pas de question aujourd'hui ! 😴"
except Exception as e:
    st.error("⚠️ Problème de connexion au Google Sheet. Vérifie les noms des onglets.")
    st.stop()

# --- AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.title("🏢 Meca 27")
    mode = st.radio("Option :", ["Connexion", "Inscription"], horizontal=True)
    
    with st.container(border=True):
        if mode == "Connexion":
            user_sel = st.selectbox("Qui es-tu ?", ["Choisir mon nom..."] + liste_noms)
            mdp_saisi = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter 🔓", use_container_width=True):
                user_row = df_users[df_users["Nom"] == user_sel]
                if not user_row.empty and str(mdp_saisi) == str(user_row["password"].values[0]):
                    st.session_state.user = user_sel
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        else:
            new_nom = st.text_input("Nouveau Surnom")
            new_mdp = st.text_input("Nouveau Mot de passe", type="password")
            if st.button("Créer mon compte ✨", use_container_width=True):
                if new_nom and new_mdp and new_nom not in liste_noms:
                    nv = pd.DataFrame([{"Nom": new_nom, "password": new_mdp}])
                    conn.update(worksheet="Utilisateurs", data=pd.concat([df_users, nv], ignore_index=True))
                    st.session_state.user = new_nom
                    st.cache_data.clear()
                    st.rerun()
                else: st.error("Nom déjà pris ou invalide.")

else:
    # --- INTERFACE ---
    demain = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    temps_restant = demain - datetime.now()
    h, r = divmod(temps_restant.seconds, 3600)
    m, _ = divmod(r, 60)
    
    st.markdown(f"<p style='text-align:right; color:gray;'>⏳ Fin du vote : {h}h {m}min</p>", unsafe_allow_html=True)
    st.write(f"Salut **{st.session_state.user}** !")

    tab1, tab2 = st.tabs(["🗳️ Vote", "💬 Chat"])

    with tab1:
        st.markdown(f"<h3 style='text-align:center;'>{question_actuelle}</h3>", unsafe_allow_html=True)
        deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values if not df_votes.empty else False

        if not deja_vote and "Pas de question" not in question_actuelle:
            choix = st.radio("Désigne ta cible :", liste_noms, horizontal=True)
            if st.button("Confirmer mon vote", use_container_width=True):
                nv_v = pd.DataFrame([{"Votant": st.session_state.user, "Cible": choix}])
                conn.update(worksheet="Votes", data=pd.concat([df_votes, nv_v], ignore_index=True))
                st.rerun()
        else:
            if not df_votes.empty:
                counts = df_votes["Cible"].value_counts().reset_index()
                counts.columns = ["Nom", "Votes"]
                # Graphique Barres épuré
                fig = px.bar(counts, x="Votes", y="Nom", orientation='h', text="Votes")
                fig.update_layout(xaxis={'visible': False}, yaxis={'title': ''}, height=300, margin=dict(t=0, b=0, l=0, r=0))
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        chat_box = st.container(height=300, border=True)
        with chat_box:
            for _, row in df_chat.iloc[::-1].iterrows():
                st.markdown(f"**{row['Utilisateur']}** : {row['Message']}")
        
        with st.form("chat_form", clear_on_submit=True):
            m = st.text_input("Ton message...")
            if st.form_submit_button("Envoyer") and m:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": m, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- FOOTER ---
    st.divider()
    if st.button("Déconnexion 🚪"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
