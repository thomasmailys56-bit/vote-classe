import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Vote Classe", page_icon="🗳️")

# --- CONNEXION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # On lit le premier onglet disponible, peu importe son nom
    df_eleves = conn.read() 
    
    # On vérifie si la colonne 'Nom' existe
    if "Nom" in df_eleves.columns:
        liste_eleves = df_eleves["Nom"].dropna().tolist()
    else:
        st.error("Je ne trouve pas de colonne nommée 'Nom' dans ton fichier !")
        st.stop()
except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.stop()

# --- RESTE DE L'INTERFACE ---
st.title("🏫 Le Vote de la Classe")

moi = st.selectbox("Qui es-tu ?", ["Sélectionne ton nom"] + liste_eleves)

if moi != "Sélectionne ton nom":
    st.subheader("Qui est le plus en retard ?")
    
    cols = st.columns(2)
    for i, eleve in enumerate(liste_eleves):
        with cols[i % 2]:
            if st.button(f"Voter pour {eleve}", key=eleve):
                st.success(f"Vote pour {eleve} pris en compte !")
                # Note : Pour l'instant le vote est visuel, on verra l'enregistrement après
