import streamlit as st
import cervello
import os

# Configurazione Pagina Mobile
st.set_page_config(
    page_title="Cervello Mobile",
    page_icon="🧠",
    layout="centered"
)

# CSS personalizzato per rendere i bottoni grandi (facili da cliccare col pollice)
st.markdown("""
    <style>
    div.stButton > button:first-child {
        height: 3em;
        width: 100%;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🧠 Assistente IA")
st.write("Scrivi e memorizza i tuoi pensieri.")

# Input di testo (sostituisce il microfono che non va sul web)
input_utente = st.text_input("Cosa vuoi dirmi?", placeholder="Esempio: Ricorda la password della palestra è 5566")

if st.button("🚀 ELABORA"):
    if input_utente:
        # Salviamo l'input per il modulo cervello
        with open("input_recente.txt", "w", encoding="utf-8") as f:
            f.write(input_utente)
        
        with st.spinner("Sto pensando..."):
            # Chiamiamo la logica di Groq
            risposta = cervello.elabora_concetto()
            st.success("Operazione completata!")
            # Se cervello.py restituisce la risposta, la mostriamo qui
            if risposta:
                st.chat_message("assistant").write(risposta)
    else:
        st.warning("Ehi, scrivi qualcosa prima!")

# Visualizzazione della memoria attuale
if st.expander("📂 Guarda la tua memoria"):
    memoria = cervello.carica_memoria()
    st.json(memoria)
