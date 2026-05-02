import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. JAVASCRIPT AGGRESSIVO (Per eliminare badge e barre extra) ---
# Questo script gira nel browser e rimuove forzatamente gli elementi in basso a destra
st.components.v1.html("""
    <script>
    const removeElements = () => {
        // Rimuove il badge di Streamlit Cloud (la corona)
        const badge = window.parent.document.querySelector(".viewerBadge_container__1QSob");
        if (badge) badge.remove();
        
        // Rimuove la barra di deploy/notifica se presente
        const deployBtn = window.parent.document.querySelector(".stDeployButton");
        if (deployBtn) deployBtn.remove();
        
        // Rimuove eventuali toolbar in basso
        const toolbar = window.parent.document.querySelector('footer');
        if (toolbar) toolbar.style.display = 'none';
    };
    
    // Esegui subito e poi ogni secondo per sicurezza
    removeElements();
    setInterval(removeElements, 1000);
    </script>
""", height=0)

# --- 3. CSS COMPLETO ---
st.markdown("""
    <style>
        /* Nasconde tutto ciò che è superfluo */
        header, footer, #MainMenu, .stDeployButton, .viewerBadge_container__1QSob {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Layout ottimizzato per mobile */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }

        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 3rem !important;
        }

        .main-title {
            font-size: 2.2rem;
            font-weight: 800;
            text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        
        .sub-title {
            text-align: center;
            color: #636E72;
            font-size: 0.8rem;
            margin-bottom: 1rem;
        }

        div.stButton > button {
            border-radius: 12px;
            background-color: #6C5CE7;
            color: white;
            font-weight: 600;
            height: 3rem;
            border: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DATI ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = {"password": p, "history": []}
    with open("utenti.json", "w") as f: json.dump(db, f)

def salva_cronologia(u, history):
    db = carica_utenti()
    if u in db:
        db[u]["history"] = history
        with open("utenti.json", "w") as f: json.dump(db, f)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
if 'utente_attuale' not in st.session_state:
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 6. INTERFACCIA ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.05, 0.9, 0.05])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Estensione della tua memoria</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("ACCEDI", use_container_width=True):
                db = carica_utenti()
                if u in db and (isinstance(db[u], dict) and db[u].get("password") == p):
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.session_state.chat_history = db[u].get("history", [])
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        
        with t2:
            nuovo_u = st.text_input("Scegli Username", key="reg_u")
            nuovo_p = st.text_input("Scegli Password", type="password", key="reg_p")
            if st.button("CREA ACCOUNT", use_container_width=True):
                if nuovo_u and nuovo_p:
                    salva_utente(nuovo_u, nuovo_p)
                    st.success("Fatto! Ora accedi.")

else:
    # --- 7. SIDEBAR ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.utente_attuale}**")
        scelta = st.radio("Menu", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        if st.button("Logout"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. CHAT ---
    if scelta == "💬 Chat":
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            try:
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.chat_message("assistant").write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                salva_cronologia(st.session_state.utente_attuale, st.session_state.chat_history)
            except Exception as e:
                st.error(f"Errore: {e}")

    # --- 9. MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Archivio Memoria")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"): st.write(v)
        else: st.info("Memoria vuota.")

    # --- 10. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        if st.button("🗑️ Svuota Chat"):
            st.session_state.chat_history = []
            salva_cronologia(st.session_state.utente_attuale, [])
            st.rerun()
