import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import random
import plotly.express as px

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Meca 27 - ECN", page_icon="🗳️", layout="centered")

# STYLE CSS (Interface Mobile, Chat & Badges)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; background-color: white; border-radius: 20px; 
        padding: 10px 20px; border: 1px solid #ddd; color: #555;
    }
    .stTabs [aria-selected="true"] { background-color: #007BFF !important; color: white !important; border: none; }
    
    /* Bulles de Chat */
    [data-testid="stChatMessage"] { background-color: #f1f3f4 !important; border-radius: 15px; margin-bottom: 10px; }
    [data-testid="stChatMessage"] p { color: #1f1f1f !important; }
    
    /* Boutons et formulaires */
    div[data-testid="stForm"] { border: none; padding: 0; }
    .stButton>button { border-radius: 12px; height: 3em; }
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
    
    # Gestion des dates
    date_auj_dt = datetime.now()
    date_aujourdhui = date_auj_dt.strftime("%d/%m/%Y")
    date_demain = (date_auj_dt + timedelta(days=1)).strftime("%d/%m/%Y")
    minuit_demain = (date_auj_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Question du jour
    df_q["Date"] = df_q["Date"].astype(str)
    q_row = df_q[df_q["Date"] == date_aujourdhui]
    question_actuelle = q_row.iloc[-1]["Texte"] if not q_row.empty else "Pas de question aujourd'hui ! 😴"

except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# --- 3. LOGIQUE DES MÉDAILLES (BADGES) ---
def get_badges():
    badges = {}
    if not df_chat.empty:
        # Bavard
        top_bavard = df_chat["Utilisateur"].value_counts().idxmax()
        badges[top_bavard] = "🗣️ Bavard"
        # Oiseau de nuit (après 2h du mat)
        df_chat['H'] = df_chat['Heure'].apply(lambda x: int(x.split(':')[0]) if ':' in str(x) else 12)
        night_birds = df_chat[df_chat['H'].isin([2, 3, 4, 5])]["Utilisateur"].unique()
        for u in night_birds:
            badges[u] = badges.get(u, "") + " 🦉 Oiseau de nuit"
    return badges

all_badges = get_badges()

# --- 4. AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.title("Meca 27 • L'Appli 🛠️")
    mode = st.radio("Option :", ["Connexion", "Inscription"], horizontal=True)
    
    with st.container(border=True):
        if mode == "Connexion":
            user_sel = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
            mdp_saisi = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter 🔓", use_container_width=True):
                user_data = df_users[df_users["Nom"] == user_sel]
                if not user_data.empty and str(mdp_saisi) == str(user_data["password"].values[0]):
                    st.session_state.user = user_sel
                    st.rerun()
                else: st.error("Identifiant ou mot de passe incorrect.")
        else:
            new_nom = st.text_input("Surnom / Nom")
            new_mdp = st.text_input("Mot de passe", type="password")
            if st.button("Créer mon compte ✨", use_container_width=True):
                if new_nom and new_mdp and new_nom not in liste_noms:
                    nv = pd.DataFrame([{"Nom": new_nom, "password": new_mdp}])
                    conn.update(worksheet="Utilisateurs", data=pd.concat([df_users, nv], ignore_index=True))
                    st.session_state.user = new_nom
                    st.cache_data.clear()
                    st.rerun()
                else: st.error("Erreur : Nom déjà pris ou champ vide.")

else:
    # --- 5. INTERFACE PRINCIPALE ---
    # Compteur de temps
    diff = minuit_demain - datetime.now()
    h, r = divmod(diff.seconds, 3600)
    m, _ = divmod(r, 60)
    st.markdown(f"<div style='text-align: right; color: gray; font-size: 13px;'>⏳ Fin du vote : {h}h {m}min</div>", unsafe_allow_html=True)
    
    user_badge = all_badges.get(st.session_state.user, "")
    st.write(f"Salut **{st.session_state.user}** ! {user_badge}")
    
    tab1, tab2 = st.tabs(["🗳️ VOTE", "💬 CHAT"])

    with tab1:
        st.markdown(f"<h2 style='text-align: center;'>{question_actuelle}</h2>", unsafe_allow_html=True)
        
        deja_vote = st.session_state.user in df_votes["Votant"].astype(str).values if not df_votes.empty else False

        if not deja_vote and "Pas de question" not in question_actuelle:
            cible = st.radio("Désigne ton candidat :", liste_noms, horizontal=True)
            if st.button("Valider mon vote", use_container_width=True):
                nv_v = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                conn.update(worksheet="Votes", data=pd.concat([df_votes, nv_v], ignore_index=True))
                st.balloons()
                st.rerun()
        else:
            if not df_votes.empty:
                st.subheader("Tendances")
                counts = df_votes["Cible"].value_counts().reset_index()
                counts.columns = ["Nom", "Votes"]
                
                # Graphique épuré
                fig = px.bar(counts, x="Votes", y="Nom", orientation='h', text="Votes", color="Votes", color_continuous_scale='Blues')
                fig.update_layout(
                    xaxis={'visible': False}, yaxis={'categoryorder':'total ascending', 'title': ''},
                    showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                
                # Badges sous le graphique
                if all_badges:
                    st.write("---")
                    st.markdown("**🏅 Distinctions :**")
                    for u, b in all_badges.items():
                        st.info(f"{b} : **{u}**")

    with tab2:
        st.subheader("Discussion")
        chat_box = st.container(height=350, border=True)
        with chat_box:
            if not df_chat.empty:
                for _, row in df_chat.iloc[::-1].iterrows():
                    u_msg = row['Utilisateur']
                    me = u_msg == st.session_state.user
                    b_u = all_badges.get(u_msg, "")
                    with st.chat_message("user" if not me else "assistant"):
                        st.markdown(f"<span style='color:#000;'>**{u_msg}** {b_u} <small>{row['Heure']}</small></span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:#000;'>{row['Message']}</span>", unsafe_allow_html=True)

        with st.form("send", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            msg = c1.text_input("Message...", label_visibility="collapsed")
            if c2.form_submit_button("Envoyer") and msg:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": msg, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- 6. ADMIN ---
    st.divider()
    random.seed(int(datetime.now().strftime("%Y%m%d")))
    admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"
    st.caption(f"👑 Admin du jour : {admin_du_jour}")
    
    if st.session_state.user == admin_du_jour:
        with st.expander(f"🛠️ Question de demain ({date_demain})"):
            q_next = st.text_input("Question :")
            if st.button("Enregistrer pour demain", use_container_width=True):
                if q_next:
                    df_q_clean = df_q[df_q["Date"].astype(str) != date_demain]
                    nv_q = pd.DataFrame([{"Texte": q_next, "Date": date_demain, "Auteur": st.session_state.user}])
                    conn.update(worksheet="Question", data=pd.concat([df_q_clean, nv_q], ignore_index=True))
                    conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                    st.success("La question est prête pour demain !")
                    st.rerun()

    # --- 7. DÉCONNEXION ---
    if st.button("Déconnexion 🚪", type="secondary"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
