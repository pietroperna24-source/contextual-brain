import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Cervello Contextual", page_icon="🧠", layout="wide")

# UI Cleaner
components.html("""
    <script>
    const cleanUI = () => {
        const elements = [".viewerBadge_container__1QSob", ".stDeployButton", "footer", "#MainMenu", "header"];
        elements.forEach(s => {
            const el = window.parent.document.querySelector(s);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(cleanUI, 500);
    </script>
""", height=0)

def carica_db():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f: json.dump(db, f, indent=4)

if 'autenticato' not in st.session_state:
    st.session_state.update({'autenticato': False, 'utente_attuale': None, 'chat_history': []})

if not st.session_state.autenticato:
    st.markdown("<h1 style='text-align: center;'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
    
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("ACCEDI"):
            db = carica_db()
            if u in db and db[u].get("pass") == p:
                st.session_state.update({'autenticato': True, 'utente_attuale': u, 'chat_history': db[u].get("history", [])})
                st.rerun()
            else: st.error("Credenziali errate")

    with t2:
        nuovo_u = st.text_input("Nuovo Username", key="r_u")
        nuovo_p = st.text_input("Nuova Password", type="password", key="r_p")
        if st.button("REGISTRATI"):
            if nuovo_u and nuovo_p:
                db = carica_db()
                db[nuovo_u] = {"pass": nuovo_p, "history": []}
                salva_db(db)
                st.success("Registrazione completata!")
else:
    st.sidebar.title(f"Benvenuto, {st.session_state.utente_attuale}")
    if st.sidebar.button("Logout"):
        st.session_state.autenticato = False
        st.rerun()

    # Chat Interface
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Scrivi qui o impartisci un comando..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
        
        st.session_state.chat_history.append({"role": "assistant", "content": risposta})
        with st.chat_message("assistant"): st.write(risposta)
        
        # Aggiorna cronologia nel DB
        db = carica_db()
        db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
        salva_db(db)
