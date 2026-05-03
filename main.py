import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- JS KILLER (Rimuove badge e icone dal browser/WebView) ---
components.html("""
    <script>
    const cleanUI = () => {
        const elementsToRemove = [
            ".viewerBadge_container__1QSob", 
            ".stDeployButton", 
            "footer", 
            "#MainMenu",
            "header"
        ];
        elementsToRemove.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(cleanUI, 500);
    </script>
""", height=0)

# --- CSS PER ARMONIA E PULIZIA ---
st.markdown("""
    <style>
        header, footer, .stDeployButton { visibility: hidden !important; height: 0; }
        .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
        .block-container { padding: 1rem !important; }
        .main-title {
            font-size: 2.2rem; font-weight: 800; text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        div.stButton > button {
            border-radius: 15px; background-color: #6C5CE7; color: white;
            height: 3.5rem; width: 100%; border: none; font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGICA DATI ---
def carica_db():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f: json.dump(db, f, indent=4)

if 'autenticato' not in st.session_state:
    st.session_state.update({'autenticato': False, 'utente_attuale': None, 'chat_history': []})

# --- INTERFACCIA ---
if not st.session_state.autenticato:
    st.markdown("<h1 class='main-title'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("ACCEDI"):
            db = carica_db()
            if u in db and db[u].get("pass") == p:
                st.session_state.update({'autenticato': True, 'utente_attuale': u, 'chat_history': db[u].get("history", [])})
                st.rerun()
    with t2:
        nuovo_u = st.text_input("Nuovo Username", key="r_u")
        nuovo_p = st.text_input("Nuova Password", type="password", key="r_p")
        if st.button("REGISTRATI"):
            if nuovo_u and nuovo_p:
                db = carica_db(); db[nuovo_u] = {"pass": nuovo_p, "history": []}; salva_db(db)
                st.success("Fatto!")
else:
    # Sezione Chat (omessa per brevità, usa la logica dei messaggi precedente)
    st.sidebar.write(f"Utente: {st.session_state.utente_attuale}")
    if st.sidebar.button("Logout"):
        st.session_state.autenticato = False
        st.rerun()
