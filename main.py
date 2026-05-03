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

# --- 2. CSS CUSTOM (Più affidabile del JS per nascondere elementi) ---
st.markdown("""
    <style>
        /* Nasconde header, footer e tasto deploy */
        header, footer, .stDeployButton, .viewerBadge_container__1QSob { display: none !important; }
        #MainMenu { visibility: hidden; }
        
        .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
        .main-title {
            font-size: 2.5rem; font-weight: 800; text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 2rem;
        }
        div.stButton > button {
            border-radius: 15px; background-color: #6C5CE7; color: white;
            height: 3.5rem; width: 100%; border: none; font-weight: 600;
        }
        .stTextInput input { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. GESTIONE DATABASE UTENTI ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    try:
        with open("utenti.json", "w") as f: json.dump(db, f, indent=4)
    except Exception as e:
        st.error(f"Errore di salvataggio: {e}")

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({'autenticato': False, 'utente': None, 'history': []})

# --- 5. UI ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    _, col_c, _ = st.columns([0.05, 0.9, 0.05])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDI"):
                db = carica_utenti()
                if u in db and db[u].get("pass") == p:
                    st.session_state.update({
                        'autenticato': True, 
                        'utente': u, 
                        'history': db[u].get('history', [])
                    })
                    st.rerun()
                else: st.error("Credenziali errate")
        
        with t2:
            nuovo_u = st.text_input("Scegli Username", key="r_u")
            nuovo_p = st.text_input("Scegli Password", type="password", key="r_p")
            if st.button("CREA ACCOUNT"):
                if nuovo_u and nuovo_p:
                    db = carica_utenti()
                    if nuovo_u in db:
                        st.error("Utente già esistente!")
                    else:
                        db[nuovo_u] = {"pass": nuovo_p, "history": []}
                        salva_db(db)
                        st.success("Registrato! Effettua il login.")

else:
    # --- 6. INTERFACCIA CHAT ---
    st.sidebar.title(f"👤 {st.session_state.utente}")
    scelta = st.sidebar.radio("Vai a", ["Chat", "Memoria"])
    
    if st.sidebar.button("Logout"):
        st.session_state.autenticato = False
        st.rerun()

    if scelta == "Chat":
        # Visualizza storico
        for msg in st.session_state.history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Parlami..."):
            # Aggiungi messaggio utente
            st.session_state.history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            # Elaborazione risposta
            with st.spinner("Pensando..."):
                risposta = cervello.elabora_concetto(st.session_state.utente, prompt)
            
            # Aggiungi risposta assistente
            st.chat_message("assistant").write(risposta)
            st.session_state.history.append({"role": "assistant", "content": risposta})
            
            # Salvataggio storia nel DB
            db = carica_utenti()
            if st.session_state.utente in db:
                db[st.session_state.utente]["history"] = st.session_state.history
                salva_db(db)

    elif scelta == "Memoria":
        st.header("🧠 Archivio Memoria")
        mem = cervello.carica_memoria(st.session_state.utente)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"): st.write(v)
        else: st.info("Memoria vuota.")
