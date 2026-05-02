import streamlit as st
import cervello # Modulo personalizzato per l'elaborazione
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual PRO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded" # Ora la sidebar è aperta di default
)

# --- 2. JS & CSS PER UI AVANZATA ---
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

st.markdown("""
    <style>
        /* Sfondo e Font */
        .stApp { background-color: #F8F9FA; }
        
        /* Personalizzazione Sidebar */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E0E0E0;
            padding-top: 2rem;
        }

        /* Titoli e Testi */
        .main-title {
            font-size: 2.2rem; font-weight: 800; color: #2D3436;
            margin-bottom: 0.5rem; text-align: center;
        }
        .memoria-item {
            padding: 10px; border-radius: 8px; background: #F1F2F6;
            margin-bottom: 5px; font-size: 0.9rem; border-left: 3px solid #6C5CE7;
        }
        
        /* Bottoni */
        div.stButton > button {
            border-radius: 10px; font-weight: 600;
            transition: all 0.3s ease;
        }
        .stChatInputContainer { padding-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. GESTIONE DATABASE ---
def carica_db():
    if not os.path.exists("utenti.json"):
        db = {"admin": {"pass": "admin123", "history": [], "role": "admin"}}
        salva_db(db)
        return db
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f:
        json.dump(db, f, indent=4)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': []
    })

# --- 5. LOGICA DI ACCESSO ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 Login", "📝 Registrati"])
        
        with tab_log:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDI"):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True,
                        'utente_attuale': u,
                        'role': db[u].get("role", "user"),
                        'chat_history': db[u].get("history", [])
                    })
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        
        with tab_reg:
            new_u = st.text_input("Nuovo Username")
            new_p = st.text_input("Nuova Password", type="password")
            if st.button("CREA ACCOUNT"):
                if new_u and new_p:
                    db = carica_db()
                    if new_u not in db:
                        db[new_u] = {"pass": new_p, "history": [], "role": "user"}
                        salva_db(db)
                        st.success("Registrato! Ora fai il login.")
                    else: st.warning("Username occupato.")

else:
    # --- 6. SIDEBAR: IL TUO CATALOGO ---
    with st.sidebar:
        st.markdown(f"### 👋 Benvenuto, {st.session_state.utente_attuale}")
        st.caption(f"Ruolo: {st.session_state.role.capitalize()}")
        st.write("---")

        # MENU DI NAVIGAZIONE
        menu = st.selectbox("Vai a:", ["💬 Chat AI", "⚙️ Impostazioni"])
        
        if st.session_state.role == "admin":
            if st.button("🛡️ Pannello Amministratore", use_container_width=True):
                st.session_state.page = "admin"
            else: st.session_state.page = "app"
        else:
            st.session_state.page = "app"

        st.write("---")
        
        # CATALOGO MEMORIE (Visualizzazione rapida)
        st.markdown("#### 📚 Catalogo Memorie")
        try:
            memorie = cervello.carica_memoria(st.session_state.utente_attuale)
            if memorie:
                for chiave in list(memorie.keys())[:5]: # Mostra le ultime 5
                    st.markdown(f"<div class='memoria-item'>{chiave}</div>", unsafe_allow_html=True)
                if st.button("Vedi tutte le memorie"):
                    st.session_state.view_mem = True
            else:
                st.info("Nessun dato salvato.")
        except:
            st.caption("Modulo memoria non disponibile.")

        st.write("---")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. CONTENUTO PRINCIPALE ---
    
    # PAGINA AMMINISTRATORE
    if st.session_state.role == "admin" and st.session_state.get("page") == "admin":
        st.title("🛡️ Dashboard Amministrazione")
        db = carica_db()
        
        col1, col2 = st.columns(2)
        col1.metric("Utenti Registrati", len(db))
        col2.metric("Attività Database", "Online")

        st.write("### Lista Utenti")
        for user, info in db.items():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{user}**")
            c2.write(f"Ruolo: {info['role']}")
            if user != "admin":
                if c3.button("Elimina", key=f"del_{user}"):
                    del db[user]
                    salva_db(db)
                    st.rerun()

    # PAGINA CHAT / MEMORIA (APP PRINCIPALE)
    elif menu == "💬 Chat AI":
        st.markdown(f"<h2 style='text-align: center;'>🧠 {st.session_state.utente_attuale.capitalize()}'s Brain</h2>", unsafe_allow_html=True)
        
        # Visualizzazione Memoria se cliccato "Vedi tutte"
        if st.session_state.get("view_mem"):
            with st.expander("📂 Archivio Completo Memorie", expanded=True):
                full_mem = cervello.carica_memoria(st.session_state.utente_attuale)
                for k, v in full_mem.items():
                    st.write(f"**{k}**: {v}")
                if st.button("Chiudi Archivio"):
                    st.session_state.view_mem = False
                    st.rerun()

        # Chat interface
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if prompt := st.chat_input("Chiedi qualcosa o memorizza un concetto..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    # Salva cronologia
                    db = carica_db()
                    db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                    salva_db(db)
                except Exception as e:
                    st.error(f"Errore: {e}")

    # PAGINA IMPOSTAZIONI
    elif menu == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        st.subheader("Gestione Dati Personali")
        if st.button("🗑️ Cancella tutta la cronologia chat"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Cronologia eliminata!")
            st.rerun()
        
        st.write("---")
        st.caption("Versione Contextual Brain 2.0 - Powered by Cervello Engine")
