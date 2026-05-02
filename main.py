import streamlit as st
import cervello 
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual PRO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UI CLEANUP (JS) ---
components.html("""
    <script>
    const cleanUI = () => {
        const elementsToRemove = [".viewerBadge_container__1QSob", ".stDeployButton", "footer", "header"];
        elementsToRemove.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(cleanUI, 500);
    </script>
""", height=0)

# --- 3. CSS CUSTOM ---
st.markdown("""
    <style>
        .stApp { background-color: #F8F9FA; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
        .main-title { font-size: 2.2rem; font-weight: 800; color: #2D3436; text-align: center; }
        .memoria-item { 
            padding: 8px; border-radius: 5px; background: #F1F2F6; 
            margin-bottom: 5px; font-size: 0.85rem; border-left: 3px solid #6C5CE7;
        }
        /* Stile per il tasto Indietro */
        .back-btn { margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DATI ---
def carica_db():
    if not os.path.exists("utenti.json"):
        db = {"admin": {"pass": "admin123", "history": [], "role": "admin"}}
        with open("utenti.json", "w") as f: json.dump(db, f, indent=4)
        return db
    with open("utenti.json", "r") as f: return json.load(f)

def salva_db(db):
    with open("utenti.json", "w") as f: json.dump(db, f, indent=4)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': [],
        'pagina_attiva': 'chat' # Pagina di default
    })

# --- 6. LOGICA ACCESSO ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Login", "📝 Registrati"])
        with t_log:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDI"):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True, 'utente_attuale': u,
                        'role': db[u].get("role", "user"),
                        'chat_history': db[u].get("history", [])
                    })
                    st.rerun()
                else: st.error("Credenziali errate")
        with t_reg:
            nu = st.text_input("Nuovo Username")
            np = st.text_input("Nuova Password", type="password")
            if st.button("CREA ACCOUNT"):
                db = carica_db()
                if nu not in db:
                    db[nu] = {"pass": np, "history": [], "role": "user"}
                    salva_db(db)
                    st.success("Fatto! Accedi ora.")

else:
    # --- 7. SIDEBAR (NAVIGAZIONE) ---
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Profilo: {st.session_state.role}")
        
        st.write("---")
        # Pulsanti di Navigazione
        if st.button("💬 Chat Principale", use_container_width=True):
            st.session_state.pagina_attiva = "chat"
            st.rerun()

        if st.button("🧠 Archivio Memoria", use_container_width=True):
            st.session_state.pagina_attiva = "memoria"
            st.rerun()

        if st.session_state.role == "admin":
            if st.button("🛡️ Pannello Admin", use_container_width=True):
                st.session_state.pagina_attiva = "admin"
                st.rerun()

        st.write("---")
        if st.button("⚙️ Impostazioni", use_container_width=True):
            st.session_state.pagina_attiva = "settings"
            st.rerun()

        if st.button("🚪 Esci", use_container_width=True, type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. LOGICA PAGINE CON TASTO INDIETRO ---

    # --- PAGINA: ADMIN ---
    if st.session_state.pagina_attiva == "admin" and st.session_state.role == "admin":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
            
        st.title("🛡️ Gestione Sistema")
        db = carica_db()
        st.write("### Utenti Attivi")
        for user, info in db.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"👤 **{user}** ({info['role']})")
            col2.write(f"💬 {len(info['history'])} msg")
            if user != "admin" and col3.button("Elimina", key=f"del_{user}"):
                del db[user]
                salva_db(db)
                st.rerun()

    # --- PAGINA: MEMORIA ---
    elif st.session_state.pagina_attiva == "memoria":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
            
        st.title("📂 Archivio Memoria")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"): st.write(v)
            else: st.info("Nessuna memoria trovata.")
        except: st.error("Errore nel caricamento memoria.")

    # --- PAGINA: IMPOSTAZIONI ---
    elif st.session_state.pagina_attiva == "settings":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
            
        st.title("⚙️ Impostazioni")
        if st.button("🗑️ Svuota Cronologia Chat"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Cronologia cancellata!")

    # --- PAGINA: CHAT (DEFAULT) ---
    else:
        st.markdown(f"<h2 style='text-align: center;'>🧠 Brain Chat</h2>", unsafe_allow_html=True)
        
        # Mostra messaggi
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        # Input
        if prompt := st.chat_input("Chiedi o memorizza..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)

            try:
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                with st.chat_message("assistant"): st.write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                db = carica_db()
                db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                salva_db(db)
            except Exception as e:
                st.error(f"Errore: {e}")
aggiungi tutti le modifiche e le modifiche in questo code e me lo mandi tutto completo modificato e funzionante
