import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random
import plotly.express as px  # <--- Nouveau pour les graphiques

st.set_page_config(page_title="Vote & Chat Classe", page_icon="💬", layout="centered")

# --- STYLE CSS PERSONNALISÉ ---
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 10px 10px 0px 0px; padding: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ff4b4b !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_users = conn.read(worksheet="Utilisateurs", ttl=0)
    df_votes = conn.read(worksheet="Votes", ttl=0)
    df_q = conn.read(worksheet="Question", ttl=0)
    try:
        df_chat = conn.read(worksheet="Messages", ttl=0)
    except:
        df_chat = pd.DataFrame(columns=["Utilisateur", "Message", "Heure"])
    liste_noms = df_users["Nom"].dropna().unique().tolist()
    question_actuelle = df_q.iloc[-1]["Texte"] if not df_q.empty else "Pas de question !"
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
random.seed(int(datetime.now().strftime("%Y%m%d")))
admin_du_jour = random.choice(liste_noms) if liste_noms else "Aucun"

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
    st.title(f"Salut {st.session_state.user} ! 👋")
    
    tab1, tab2 = st.tabs(["📊 RÉSULTATS & VOTE", "💬 DISCUSSION"])

    with tab1:
        st.info(f"✨ **Question :** {question_actuelle}")
        a_vote = st.session_state.user in df_votes["Votant"].astype(str).values

        if not a_vote:
            st.subheader("Donne ton vote")
            cible = st.radio("Désigne quelqu'un :", liste_noms, key="radio_vote", horizontal=True)
            if st.button("Valider mon vote 🗳️", key="btn_vote", use_container_width=True):
                nouveau = pd.DataFrame([{"Votant": st.session_state.user, "Cible": cible}])
                conn.update(worksheet="Votes", data=pd.concat([df_votes, nouveau], ignore_index=True))
                st.balloons()
                st.rerun()
        else:
            st.success("✅ Ton vote a été pris en compte !")
            if not df_votes.empty:
                # --- GRAPHIQUE PLOTLY ---
                df_counts = df_votes["Cible"].value_counts().reset_index()
                df_counts.columns = ["Nom", "Votes"]
                
                fig = px.bar(df_counts, x="Nom", y="Votes", 
                             color="Votes", 
                             color_continuous_scale='Reds',
                             text="Votes")
                
                fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                  xaxis_title="", yaxis_title="", showlegend=False, height=350)
                fig.update_traces(textposition='outside', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.8)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Petit podium
                top_name = df_counts.iloc[0]["Nom"]
                st.markdown(f"<h3 style='text-align: center;'>🏆 Leader : {top_name}</h3>", unsafe_allow_html=True)

    with tab2:
        st.subheader("Le Mur de la Classe")
        
        # Zone de messages avec défilement
        chat_zone = st.container(height=400, border=True)
        with chat_zone:
            if not df_chat.empty:
                for i, row in df_chat.iloc[::-1].iterrows():
                    is_me = row['Utilisateur'] == st.session_state.user
                    with st.chat_message("user" if not is_me else "assistant"):
                        st.write(f"**{row['Utilisateur']}** • {row['Heure']}")
                        st.write(row['Message'])
            else:
                st.write("Aucun message...")

        # Formulaire d'envoi collé en bas
        with st.form("chat_form", clear_on_submit=True):
            cols = st.columns([4, 1])
            msg_texte = cols[0].text_input("Message...", label_visibility="collapsed")
            submit = cols[1].form_submit_button("Envoyer")
            
            if submit and msg_texte:
                nouveau_msg = pd.DataFrame([{"Utilisateur": st.session_state.user, "Message": msg_texte, "Heure": datetime.now().strftime("%H:%M")}])
                conn.update(worksheet="Messages", data=pd.concat([df_chat, nouveau_msg], ignore_index=True))
                st.rerun()

    # --- FOOTER / ADMIN ---
    st.divider()
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.write(f"👑 Admin du jour : **{admin_du_jour}**")
    with col_b:
        if st.button("Déconnexion", key="btn_logout", use_container_width=True):
            del st.session_state.user
            st.rerun()

    if st.session_state.user == admin_du_jour:
        deja_fait = not df_q.empty and date_aujourdhui in df_q["Date"].astype(str).values
        if not deja_fait:
            with st.expander("⚙️ OPTIONS ADMINISTRATEUR"):
                nouvelle_q = st.text_input("Question de demain :", key="in_admin")
                if st.button("Lancer la nouvelle question", key="bt_admin", use_container_width=True):
                    df_nouvelle_q = pd.DataFrame([{"Texte": nouvelle_q, "Date": date_aujourdhui, "Auteur": st.session_state.user}])
                    conn.update(worksheet="Question", data=pd.concat([df_q, df_nouvelle_q], ignore_index=True))
                    conn.update(worksheet="Votes", data=pd.DataFrame(columns=["Votant", "Cible"]))
                    st.rerun()
