import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random
import plotly.express as px
import streamlit as st

# --- CONFIGURATION PRO ---
# Remplace par le lien direct vers ton logo GitHub
LOGO_URL = "https://raw.githubusercontent.com/ton-pseudo/ton-repo/main/logo.png"

st.set_page_config(
    page_title="Meca 27 - ECN",
    page_icon=LOGO_URL,
    layout="centered"
)

# Injection pour l'installation sur mobile (icône écran d'accueil)
st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-title" content="Meca 27">
    </head>
    """, unsafe_allow_html=True)

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Vote & Chat Classe", page_icon="💬", layout="centered")

# Style pour les onglets
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 10px 10px 0px 0px; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONNEXION ET LECTURE (MÉTHODE RAPIDE)
SHEET_ID = "1UwQo0lpHDbHw8utmpx5KEmgW0sEHI4opudIHaFRx9nc"

def read_sheet_fast(sheet_name):
    # Lecture via URL pour éviter l'erreur de Quota 429
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

# Connexion pour l'écriture (Update)
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
    question_actuelle = df_q.iloc[-1]["Texte"] if not df_q.empty else "Pas de question !"
except Exception as e:
    st.error(f"Erreur de lecture : {e}")
    st.stop()

# 3. LOGIQUE ADMIN DU JOUR
date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
random.seed(int(datetime.now().strftime("%Y%m%d")))
admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"

# 4. SYSTÈME DE CONNEXION
if 'user' not in st.session_state:
    st.title("Connexion 🔒")
    user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
    mdp_saisi = st.text_input("Mot de passe", type="password", key="login_mdp")
    
    if st.button("Se connecter", key="login_btn", use_container_width=True):
        user_data = df_users[df_users["Nom"] == user_choisi]
        if not user_data.empty and str(mdp_saisi) == str(user_data["password"].values[0]):
            st.session_state.user = user_choisi
            st.rerun()
        else:
            st.error("Nom ou mot de passe incorrect")
else:
    # --- INTERFACE PRINCIPALE ---
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    tab1, tab2 = st.tabs(["📊 VOTE & RÉSULTATS", "💬 DISCUSSION"])

    # --- ONGLET 1 : VOTE ---
    with tab1:
        st.info(f"✨ **Question :** {question_actuelle}")
        
        # On vérifie si l'utilisateur a déjà voté (on force en string pour comparer)
        deja_vote = False
        if not df_votes.empty:
            deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values

        if not deja_vote:
            cible = st.radio("Ton choix :", liste_noms, key="radio_vote", horizontal=True)
            if st.button("Valider mon vote 🗳️", key="btn_vote", use_container_width=True):
                nouveau_v = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                conn.update(worksheet="Votes", data=pd.concat([df_votes, nouveau_v], ignore_index=True))
                st.balloons()
                st.rerun()
        else:
            st.success("✅ Tu as déjà voté !")
            if not df_votes.empty:
                df_counts = df_votes["Cible"].value_counts().reset_index()
                df_counts.columns = ["Nom", "Votes"]
                
                fig = px.bar(df_counts, x="Nom", y="Votes", color="Votes", 
                             color_continuous_scale='Reds', text="Votes")
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # --- ONGLET 2 : CHAT ---
    with tab2:
        st.subheader("Le Mur de la Classe")
        
        # Zone de messages
        chat_zone = st.container(height=350, border=True)
        with chat_zone:
            if not df_chat.empty:
                for i, row in df_chat.iloc[::-1].iterrows():
                    is_me = row['Utilisateur'] == st.session_state.user
                    with st.chat_message("user" if not is_me else "assistant"):
                        st.write(f"**{row['Utilisateur']}** • {row['Heure']}")
                        st.write(row['Message'])
            else:
                st.write("Aucun message...")

        # Envoi de message
        with st.form("chat_form", clear_on_submit=True):
            cols = st.columns([4, 1])
            msg_txt = cols[0].text_input("Ton message...", label_visibility="collapsed")
            if cols[1].form_submit_button("Envoyer") and msg_txt:
                nouveau_m = pd.DataFrame([{"Utilisateur": st.session_state.user, 
                                           "Message": msg_txt, 
                                           "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nouveau_m], ignore_index=True))
                st.rerun()

   # --- SECTION ADMIN ---
    st.divider()
    
    # On compare en minuscules pour éviter les erreurs de saisie
    user_actuel = str(st.session_state.user).strip().lower()
    elu_du_jour = str(admin_du_jour).strip().lower()

    st.write(f"👑 Admin du jour : **{admin_du_jour}**")
    
    if user_actuel == elu_du_jour:
        # On vérifie si la question n'est pas déjà validée
        deja_fait = False
        if not df_q.empty:
            # On vérifie la date du jour
            deja_fait = date_aujourdhui in df_q["Date"].astype(str).values

        if not deja_fait:
            with st.expander("⚙️ OPTIONS ADMIN (Ton tour !)"):
                nouvelle_q = st.text_input("Quelle est la question de demain ?")
                if st.button("Valider la question", use_container_width=True):
                    if nouvelle_q:
                        # Mise à jour
                        df_nq = pd.DataFrame([{"Texte": nouvelle_q, "Date": date_aujourdhui, "Auteur": st.session_state.user}])
                        conn.update(worksheet="Question", data=pd.concat([df_q, df_nq], ignore_index=True))
                        # Reset
                        conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                        st.success("Question envoyée !")
                        st.rerun()
        else:
            st.info("✅ Tu as déjà choisi la question pour aujourd'hui !")
    else:
        st.write("🔒 Seul l'élu du jour peut modifier la question.")

    if st.button("Déconnexion", key="logout_btn"):
        del st.session_state.user
        st.rerun()
