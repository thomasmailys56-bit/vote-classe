import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Debug Vote", page_icon="🔍")

st.title("🔍 Test de connexion au Sheet")

try:
    # Connexion
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # On lit le sheet sans préciser d'onglet pour voir ce qui arrive
    df = conn.read()
    
    # --- ZONE DE DEBUG ---
    st.write("### Ce que Python voit dans ton fichier :")
    st.write("Colonnes trouvées :", list(df.columns))
    st.write("Aperçu des données :", df.head())
    
    if "Nom" in df.columns and "Mot de passe" in df.columns:
        st.success("✅ Connexion réussie ! Les colonnes sont correctes.")
        
        # Système de Login simple pour tester
        noms = df["Nom"].dropna().unique().tolist()
        user = st.selectbox("Choisis ton nom", noms)
        mdp = st.text_input("Mot de passe", type="password")
        
        if st.button("Tester la connexion"):
            vrai_mdp = str(df[df["Nom"] == user]["Mot de passe"].values[0])
            if str(mdp) == vrai_mdp:
                st.balloons()
                st.success(f"Bravo {user}, ça marche !")
            else:
                st.error("Mauvais mot de passe.")
    else:
        st.error("❌ Erreur : Je ne trouve pas les colonnes 'Nom' et 'Mot de passe'.")
        st.info("Vérifie que la première ligne de ton Excel contient exactement 'Nom' en A1 et 'Mot de passe' en B1.")

except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
    st.write("Vérifie que ton lien dans 'Secrets' est le bon et que le Sheet est partagé en 'Tous les utilisateurs disposant du lien'.")
