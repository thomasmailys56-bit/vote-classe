import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random
import plotly.express as px

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Meca 27 - Vote", page_icon="🗳️", layout="centered")

# CSS pour un look "Appli Mobile"
st.markdown("""
    <style>
    /* Style global */
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: white; border-radius: 20px; 
        padding: 10px 20px; border: 1px solid #ddd; color: #555;
    }
    .stTabs [aria-selected="true"] { background-color: #007BFF !important; color: white !important; border: none; }
    
    /* Cartes de messages et résultats */
    .stChatMessage { border-radius: 15px; background-color: white; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stForm"] { border: none; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LECTURE RAPIDE (ANTI-QUOTA) ---
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"

def read_sheet_fast(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = read_sheet_fast("Utilisateurs")
    df_votes = read_sheet_fast("Votes")
    df_q = read_sheet_fast("Question")
    try:
        df_chat = read_sheet_fast("Messages")
    except:
        df_chat = pd.DataFrame(columns=["Utilisateur", "Message", "Heure"])
    
    liste_noms = df_users["Nom"].dropna().unique().tolist()
    question_actuelle = df_q.iloc[-1]["Texte"] if not df_q.empty else "Pas de question pour le moment..."
except Exception as e:
    st.error(f"Connexion impossible : {e}")
    st.stop()

# --- 3. LOGIQUE ADMIN ---
date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
random.seed(int(datetime.now().strftime("%Y%m%d")))
admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"

# --- 4. AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.header("🏢 Centrale Nantes")
    st.title("Meca 27 • L'Appli")
    
    with st.container(border=True):
        user_choisi = st.selectbox("Qui es-tu ?", ["Choisir mon nom..."] + liste_noms)
        mdp_saisi = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter 🔓", use_container_width=True):
            user_data = df_users[df_users["Nom"] == user_choisi]
            if not user_data.empty and str(mdp_saisi) == str(user_data["password"].values[0]):
                st.session_state.user = user_choisi
                st.rerun()
            else:
                st.error("Accès refusé.")
else:
    # --- INTERFACE CONNECTÉE ---
    st.write(f"Utilisateur : **{st.session_state.user}**")
    
    tab1, tab2 = st.tabs(["🗳️ Vote du jour", "💬 Chat Promo"])

    with tab1:
        st.markdown(f"<h2 style='text-align: center;'>{question_actuelle}</h2>", unsafe_allow_html=True)
        
        deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values if not df_votes.empty else False

        if not deja_vote:
            with st.container(border=True):
                cible = st.radio("Désigne ton candidat :", liste_noms, horizontal=True)
                if st.button("Valider mon choix", use_container_width=True):
                    nv_vote = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                    conn.update(worksheet="Votes", data=pd.concat([df_votes, nv_vote], ignore_index=True))
                    st.balloons()
                    st.rerun()
        else:
            st.success("Vote enregistré ! Voici les tendances :")
            if not df_votes.empty:
                counts = df_votes["Cible"].value_counts().reset_index()
                counts.columns = ["Nom", "Votes"]
                
                # --- GRAPHIQUE DONUT MODERNE ---
                fig = px.pie(counts, values='Votes', names='Nom', hole=.6,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_traces(textinfo='percent+label', hoverinfo='label+value')
                fig.update_layout(showlegend=False, height=350, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Discussion")
        # Zone de chat
        chat_container = st.container(height=380, border=True)
        with chat_container:
            if not df_chat.empty:
                for _, row in df_chat.iloc[::-1].iterrows():
                    me = row['Utilisateur'] == st.session_state.user
                    with st.chat_message("user" if not me else "assistant"):
                        st.markdown(f"**{row['Utilisateur']}** <span style='font-size:10px; color:gray;'>{row['Heure']}</span>", unsafe_allow_html=True)
                        st.write(row['Message'])
            else:
                st.write("Aucun message.")

        # Champ d'envoi
        with st.form("send_msg", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            msg = c1.text_input("Message...", label_visibility="collapsed")
            if c2.form_submit_button("Envoyer") and msg:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": msg, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- SECTION ADMIN ---
    st.divider()
    st.caption(f"👑 Élu du jour : {admin_du_jour}")
    
    if st.session_state.user == admin_du_jour:
        deja_fait = not df_q.empty and date_aujourdhui in df_q["Date"].astype(str).values
        if not deja_fait:
            with st.expander("🛠️ Admin : Changer la question"):
                new_q = st.text_input("Nouvelle question :")
                if st.button("Lancer", use_container_width=True) and new_q:
                    df_nq = pd.DataFrame([{"Texte": new_q, "Date": date_aujourdhui, "Auteur": st.session_state.user}])
                    conn.update(worksheet="Question", data=pd.concat([df_q, df_nq], ignore_index=True))
                    conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                    st.rerun()

    if st.button("Se déconnecter", type="secondary"):
        del st.session_state.user
        st.rerun()
