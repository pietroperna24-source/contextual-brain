import streamlit as st
import cervello
import json
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cervello Contextual v2", page_icon="🧠", layout="wide")

# --- STILE CSS AVANZATO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextInput > div > div > input { border-radius: 20px; }
    .stButton > button { width: 100%; border-radius: 20px; transition: 0.3s; }
    .stButton > button:hover { transform: scale(1.02); background-color: #00ffcc; color: black; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e3440,#2e3440); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI UTILI ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    with open("utenti.json", "r") as f: return json.load(f)

# --- SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None

# --- LOGIN / REGISTRAZIONE ---
if not st.session_state.autenticato:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=100)
        menu = st.selectbox("Cosa vuoi fare?", ["Login", "Registrati"])
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ENTRA"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else: st.error("Credenziali errate")
else:
    # --- BARRA LATERALE (SIDEBAR) ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=80)
        st.title(f"Piacere, {st.session_state.utente_attuale}")
        scelta = st.radio("Naviga", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        
        st.write("---")
        if st.button("Esci"):
            st.session_state.autenticato = False
            st.rerun()

    # --- SEZIONE CHAT ---
    if scelta == "💬 Chat":
        st.title("💬 Chiedi al tuo Cervello")
        container = st.container()
        with container:
            input_utente = st.chat_input("Scrivi qui...")
            if input_utente:
                st.chat_message("user").write(input_utente)
                with st.spinner("Pensando..."):
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, input_utente)
                    st.chat_message("assistant").write(risposta)

    # --- SEZIONE MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Cosa ricordo di te")
        dati = cervello.carica_memoria(st.session_state.utente_attuale)
        if dati:
            for k, v in dati.items():
                st.info(f"**{k}**: {v}")
        else:
            st.write("La tua memoria è vuota.")

    # --- SEZIONE IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni Utente")
        st.subheader("Personalizzazione")
        tema = st.selectbox("Colore Tema (Simulato)", ["Dark Blue", "Emerald", "Sunset"])
        
        st.write("---")
        st.subheader("Gestione Dati")
        if st.button("⚠️ CANCELLA TUTTA LA MEMORIA"):
            file_m = f"memoria_{st.session_state.utente_attuale}.json"
            if os.path.exists(file_m):
                os.remove(file_m)
                st.success("Memoria pulita con successo!")
            else:
                st.warning("Nessun dato da cancellare.")
