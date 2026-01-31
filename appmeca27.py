import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, time
import random
import plotly.express as px

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Meca 27 - ECN", page_icon="🗳️", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stChatMessage"] { background-color: #f1f3f4 !important; border-radius: 15px; }
    [data-testid="stChatMessage"] p { color: #1f1f1f !important; }
    .stProgress > div > div > div > div { background-color: #007BFF; }
    .badge { padding: 4px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; margin-right: 5px; }
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
    date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
    date_demain_dt = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    
    q_du_jour = df_q[df_q["Date"].astype(str) == date_aujourdhui]
    question_actuelle = q_du_jour.iloc[-1]["Texte"] if not q_du_jour.empty else "Pas de question aujourd'hui ! 😴"

except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# --- 3. LOGIQUE DES TITRES (BADGES) ---
def get_badges():
    badges = {}
    # Bavard (celui qui a le plus de messages)
    if not df_chat.empty:
        top_bavard = df_chat["Utilisateur"].value_counts().idxmax()
        badges[top_bavard] = "🗣️ Le Bavard"
    
    # Oiseau de nuit (Message après 2h du matin)
    if not df_chat.empty:
        # On suppose que 'Heure' est au format HH:MM
        df_chat['H'] = df_chat['Heure'].apply(lambda x: int(x.split(':')[0]))
        night_birds = df_chat[df_chat['H'].isin([2, 3, 4, 5])]["Utilisateur"].unique()
        for user in night_birds:
            badges[user] = badges.get(user, "") + " 🦉 Oiseau de nuit"

    # Citoyen Modèle (Vote avant 9h - nécessite une colonne Heure dans Votes, on simule sur le chat ici ou par défaut)
    # Si tu ajoutes une colonne Heure dans Votes, on pourra le faire précisément.
    return badges

all_badges = get_badges()

# --- 4. AUTHENTIFICATION ---
if 'user' not in st.session_state:
    st.title("Meca 27 • L'Appli")
    mode = st.radio("Option :", ["Connexion", "Inscription"], horizontal=True)
    with st.container(border=True):
        if mode == "Connexion":
            user_choisi = st.selectbox("Qui es-tu ?", ["Choisir..."] + liste_noms)
            mdp_saisi = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True):
                user_data = df_users[df_users["Nom"] == user_choisi]
                if not user_data.empty and str(mdp_saisi) == str(user_data["password"].values[0]):
                    st.session_state.user = user_choisi
                    st.rerun()
        else:
            new_nom = st.text_input("Ton Surnom")
            new_mdp = st.text_input("Mot de passe", type="password")
            if st.button("S'inscrire", use_container_width=True):
                if new_nom and new_mdp and new_nom not in liste_noms:
                    nv_user = pd.DataFrame([{"Nom": new_nom, "password": new_mdp}])
                    conn.update(worksheet="Utilisateurs", data=pd.concat([df_users, nv_user], ignore_index=True))
                    st.session_state.user = new_nom
                    st.cache_data.clear()
                    st.rerun()

else:
    # --- 5. INTERFACE ---
    # COMPTEUR DE TEMPS
    temps_restant = date_demain_dt - datetime.now()
    heures, reste = divmod(temps_restant.seconds, 3600)
    minutes, _ = divmod(reste, 60)
    
    st.markdown(f"<div style='text-align: right; color: gray; font-size: 14px;'>⏳ Fin du vote dans : {heures}h {minutes}min</div>", unsafe_allow_html=True)
    st.write(f"Salut **{st.session_state.user}** ! {all_badges.get(st.session_state.user, '')}")
    
    tab1, tab2 = st.tabs(["🗳️ Vote", "💬 Chat"])

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
                st.subheader("Tendances actuelles")
                counts = df_votes["Cible"].value_counts().reset_index()
                counts.columns = ["Nom", "Votes"]
                
                # Graphique à Barres Horizontal
                fig = px.bar(counts, x="Votes", y="Nom", orientation='h', 
                             text="Votes", color="Votes", color_continuous_scale='Blues')
                fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                # Affichage des Badges des nominés
                st.write("---")
                st.markdown("**Médailles de la promo :**")
                for user, badge in all_badges.items():
                    st.write(f"{badge} : **{user}**")

    with tab2:
        chat_box = st.container(height=350, border=True)
        with chat_box:
            if not df_chat.empty:
                for _, row in df_chat.iloc[::-1].iterrows():
                    u = row['Utilisateur']
                    me = u == st.session_state.user
                    badge_u = all_badges.get(u, "")
                    with st.chat_message("user" if not me else "assistant"):
                        st.markdown(f"<span style='color:#000;'>**{u}** {badge_u} <small>{row['Heure']}</small></span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='color:#000;'>{row['Message']}</span>", unsafe_allow_html=True)

        with st.form("send", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            m = c1.text_input("Message...", label_visibility="collapsed")
            if c2.form_submit_button("Envoyer") and m:
                nv_m = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": m, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nv_m], ignore_index=True))
                st.rerun()

    # --- 6. ADMIN ---
    random.seed(int(datetime.now().strftime("%Y%m%d")))
    admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"
    if st.session_state.user == admin_du_jour:
        with st.expander("🛠️ Question de demain"):
            q_next = st.text_input("Question :")
            if st.button("Enregistrer"):
                date_demain = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
                df_q_clean = df_q[df_q["Date"].astype(str) != date_demain]
                nv_q = pd.DataFrame([{"Texte": q_next, "Date": date_demain, "Auteur": st.session_state.user}])
                conn.update(worksheet="Question", data=pd.concat([df_q_clean, nv_q], ignore_index=True))
                conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                st.success("Prêt pour demain !")
