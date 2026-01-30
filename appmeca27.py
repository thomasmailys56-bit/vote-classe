import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import random
import plotly.express as px

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Meca 27 - ECN", page_icon="🗳️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: white; border-radius: 20px; 
        padding: 10px 20px; border: 1px solid #ddd; color: #555;
    }
    .stTabs [aria-selected="true"] { background-color: #007BFF !important; color: white !important; border: none; }
    [data-testid="stChatMessage"] { background-color: #f1f3f4 !important; border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessage"] p { color: #1f1f1f !important; }
    div[data-testid="stForm"] { border: none; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LECTURE DES DONNÉES ---
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
    
    # Date du jour pour l'affichage
    date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
    date_demain = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    df_q["Date"] = df_q["Date"].astype(str)
    q_du_jour = df_q[df_q["Date"] == date_aujourdhui]
    
    if not q_du_jour.empty:
        question_actuelle = q_du_jour.iloc[-1]["Texte"]
    else:
        question_actuelle = "Pas de question pour aujourd'hui. Revenez demain ! 😴"

except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# --- 3. LOGIQUE ADMIN ---
random.seed(int(datetime.now().strftime("%Y%m%d")))
admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"

# --- 4. AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.header("🏢 Centrale Nantes")
    st.title("Meca 27 • L'Appli")
    mode = st.radio("Option :", ["Connexion", "Inscription"], horizontal=True)
    
    with st.container(border=True):
        if mode == "Connexion":
            user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
            mdp_saisi = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter 🔓", use_container_width=True):
                user_data = df_users[df_users["Nom"] == user_choisi]
                if not user_data.empty and str(mdp_saisi) == str(user_data["password"].values[0]):
                    st.session_state.user = user_choisi
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
        else:
            new_nom = st.text_input("Ton Surnom")
            new_mdp = st.text_input("Mot de passe", type="password")
            if st.button("Créer mon compte ✨", use_container_width=True):
                if new_nom and new_mdp and new_nom not in liste_noms:
                    nv_user = pd.DataFrame([{"Nom": new_nom, "password": new_mdp}])
                    conn.update(worksheet="Utilisateurs", data=pd.concat([df_users, nv_user], ignore_index=True))
                    st.session_state.user = new_nom
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Nom déjà pris ou champ vide.")

else:
    # --- 5. INTERFACE ---
    st.write(f"Utilisateur : **{st.session_state.user}**")
    tab1, tab2 = st.tabs(["🗳️ Vote du jour", "💬 Chat"])

    with tab1:
        st.markdown(f"<h2 style='text-align: center;'>{question_actuelle}</h2>", unsafe_allow_html=True)
        
        deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values if not df_votes.empty else False

        if not deja_vote and "Revenez demain" not in question_actuelle:
            with st.container(border=True):
                cible = st.radio("Désigne ta cible :", liste_noms, horizontal=True)
                if st.button("Valider le vote", use_container_width=True):
                    nv_v = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                    conn.update(worksheet="Votes", data=pd.concat([df_votes, nv_v], ignore_index=True))
                    st.balloons()
                    st.rerun()
        elif deja_vote:
            st.success("Résultats actuels :")
            counts = df_votes["Cible"].value_counts().reset_index()
            counts.columns = ["Nom", "Votes"]
            fig = px.pie(counts, values='Votes', names='Nom', hole=.6, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Discussion")
        chat_box = st.container(height=350, border=True)
        with chat_box:
            if not df_chat.empty:
                for _, row in df_chat.iloc[::-1].iterrows():
                    me = row['Utilisateur'] == st.session_state.user
                    with st.chat_message("user" if not me else "assistant"):
                        st.markdown(f"<span style='color:#000;'>**{row['Utilisateur']}** <small>{row['Heure']}</small></span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:#000;'>{row['Message']}</span>", unsafe_allow_html=True)

        with st.form("send", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            m = c1.text_input("Message...", label_visibility="collapsed")
            if c2.form_submit_button("Envoyer") and m:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": m, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- 6. SECTION ADMIN (POUR DEMAIN) ---
    st.divider()
    st.caption(f"👑 Admin du jour : {admin_du_jour}")
    
    if st.session_state.user == admin_du_jour:
        with st.expander(f"🛠️ Préparer la question de demain ({date_demain})"):
            q_suivante = st.text_input("Quelle sera la question de demain ?")
            if st.button("Valider pour demain", use_container_width=True):
                if q_suivante:
                    # On supprime s'il y avait déjà une question prévue pour demain
                    df_q_clean = df_q[df_q["Date"] != date_demain]
                    nv_q = pd.DataFrame([{"Texte": q_suivante, "Date": date_demain, "Auteur": st.session_state.user}])
                    conn.update(worksheet="Question", data=pd.concat([df_q_clean, nv_q], ignore_index=True))
                    
                    # On vide l'onglet Vote pour demain (facultatif ici car le reset se fait à l'affichage)
                    conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                    
                    st.success(f"C'est noté ! La question sera activée demain à minuit.")
                    st.rerun()

    if st.button("Déconnexion"):
        del st.session_state.user
        st.rerun()
