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

# --- 2. JS KILLER (Rimuove icone Android Studio/Codespaces/Streamlit) ---
components.html("""
    <script>
    const hideElements = () => {
        const selectors = [
            ".viewerBadge_container__1QSob", // Badge corona
            ".stDeployButton",               // Tasto Deploy
            "footer",                        // Footer Streamlit
            "#MainMenu",                     // Menu hamburger
            "header"                         // Header bianco
        ];
        selectors.forEach(s => {
            const el = window.parent.document.querySelector(s);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(hideElements, 500);
    </script>
""", height=0)

# --- 3. CSS CUSTOM ---
st.markdown("""
    <style>
        header, footer, .stDeployButton { visibility: hidden !important; }
        .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
        .main-title {
            font-size: 2.5rem; font-weight: 800; text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        div.stButton > button {
            border-radius: 15px; background-color: #6C5CE7; color: white;
            height: 3.5rem; width: 100%; border: none; font-weight: 600;
        }
        .stTextInput input { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. GESTIONE DATABASE UTENTI ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    with open("utenti.json", "r") as f: return json.load(f)

def salva_db(db):
    with open("utenti.json", "w") as f: json.dump(db, f, indent=4)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({'autenticato': False, 'utente': None, 'history': []})

# --- 6. UI ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.05, 0.9, 0.05])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDI"):
                db = carica_utenti()
                if u in db and db[u].get("pass") == p:
                    st.session_state.update({'autenticato': True, 'utente': u, 'history': db[u].get('history', [])})
                    st.rerun()
                else: st.error("Credenziali errate")
        
        with t2:
            nuovo_u = st.text_input("Scegli Username", key="r_u")
            nuovo_p = st.text_input("Scegli Password", type="password", key="r_p")
            if st.button("CREA ACCOUNT"):
                if nuovo_u and nuovo_p:
                    db = carica_utenti()
                    db[nuovo_u] = {"pass": nuovo_p, "history": []}
                    salva_db(db)
                    st.success("Registrato! Effettua il login.")

else:
    # --- 7. INTERFACCIA CHAT ---
    st.sidebar.title(f"👤 {st.session_state.utente}")
    scelta = st.sidebar.radio("Vai a", ["Chat", "Memoria"])
    if st.sidebar.button("Logout"):
        st.session_state.autenticato = False
        st.rerun()

    if scelta == "Chat":
        for msg in st.session_state.history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Parlami..."):
            st.session_state.history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            risposta = cervello.elabora_concetto(st.session_state.utente, prompt)
            
            st.chat_message("assistant").write(risposta)
            st.session_state.history.append({"role": "assistant", "content": risposta})
            
            # Salvataggio storia
            db = carica_utenti()
            db[st.session_state.utente]["history"] = st.session_state.history
            salva_db(db)

    elif scelta == "Memoria":
        st.header("🧠 Archivio Memoria")
        mem = cervello.carica_memoria(st.session_state.utente)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"): st.write(v)
        else: st.info("Memoria vuota.")
