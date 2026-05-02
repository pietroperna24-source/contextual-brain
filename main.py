import streamlit as st
import json
import os
import streamlit.components.v1 as components
import extra_streamlit_components as stx

# Prova a importare il modulo cervello
try:
    import cervello
except ImportError:
    # Mock per test se il modulo non esiste nel tuo ambiente locale
    class MockCervello:
        def elabora_concetto(self, u, p): return f"Risposta automatica a: {p}"
        def carica_memoria(self, u): return {"Esempio": "Dato memorizzato"}
    cervello = MockCervello()

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual Ultimate",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. GESTIONE COOKIE (Persistenza Login) ---
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()

cookie_manager = get_cookie_manager()

# --- 3. UI CLEANUP (JS) ---
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

# --- 4. CSS CUSTOM ---
st.markdown("""
    <style>
        .stApp { background-color: #F8F9FA; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
        .main-title { font-size: 2.2rem; font-weight: 800; color: #2D3436; text-align: center; margin-bottom: 0px;}
        .sub-title { text-align: center; color: #636E72; font-size: 0.9rem; margin-bottom: 2rem; }
        .mem-card { 
            padding: 12px; border-radius: 10px; background: white; 
            margin-bottom: 10px; border-left: 5px solid #6C5CE7;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        div.stButton > button {
            border-radius: 12px; font-weight: 600; transition: all 0.2s;
        }
    </style>
""", unsafe_allow_html=True)

# --- 5. FUNZIONI DATI ---
DB_FILE = "utenti.json"

def carica_db():
    if not os.path.exists(DB_FILE):
        db = {"admin": {"pass": "admin123", "history": [], "role": "admin"}}
        salva_db(db)
        return db
    with open(DB_FILE, "r") as f: return json.load(f)

def salva_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- 6. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': [],
        'pagina_attiva': 'chat'
    })

# LOGICA PERSISTENZA: Controllo Cookie
saved_user = cookie_manager.get("cervello_user_login")
if saved_user and not st.session_state.autenticato:
    db = carica_db()
    if saved_user in db:
        st.session_state.update({
            'autenticato': True,
            'utente_attuale': saved_user,
            'role': db[saved_user].get("role", "user"),
            'chat_history': db[saved_user].get("history", [])
        })

# --- 7. SCHERMATA ACCESSO ---
if not st.session_state.autenticato:
    _, col_c, _ = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Il tuo archivio cognitivo persistente</p>", unsafe_allow_html=True)
        
        t_log, t_reg = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t_log:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("ACCEDI AL SISTEMA", use_container_width=True):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    # Salva cookie per 30 giorni
                    cookie_manager.set("cervello_user_login", u)
                    st.session_state.update({
                        'autenticato': True, 'utente_attuale': u,
                        'role': db[u].get("role", "user"),
                        'chat_history': db[u].get("history", [])
                    })
                    st.rerun()
                else: st.error("Credenziali errate")
        
        with t_reg:
            nu = st.text_input("Scegli Username", key="reg_u")
            np = st.text_input("Scegli Password", type="password", key="reg_p")
            if st.button("CREA ACCOUNT", use_container_width=True):
                db = carica_db()
                if nu and nu not in db:
                    db[nu] = {"pass": np, "history": [], "role": "user"}
                    salva_db(db)
                    st.success("Account creato! Effettua il login.")

else:
    # --- 8. SIDEBAR (TENDINA SEMPRE ATTIVA) ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Status: {st.session_state.role.capitalize()}")
        st.write("---")
        
        if st.button("💬 Chat AI", use_container_width=True):
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

        if st.button("🚪 Esci (Logout)", use_container_width=True, type="primary"):
            cookie_manager.delete("cervello_user_login")
            st.session_state.autenticato = False
            st.rerun()

    # --- 9. NAVIGAZIONE E TASTO INDIETRO ---
    # Colonna superiore per tasto indietro dinamico
    if st.session_state.pagina_attiva != "chat":
        col_tit, col_back = st.columns([0.8, 0.2])
        with col_back:
            if st.button("⬅️ INDIETRO", use_container_width=True):
                st.session_state.pagina_attiva = "chat"
                st.rerun()

    # --- 10. LOGICA DELLE PAGINE ---

    # PAGINA: ADMIN
    if st.session_state.pagina_attiva == "admin" and st.session_state.role == "admin":
        st.title("🛡️ Dashboard Amministratore")
        db = carica_db()
        st.write(f"Utenti registrati: **{len(db)}**")
        for user, info in db.items():
            with st.container():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{user}** ({info['role']})")
                c2.write(f"💬 {len(info['history'])} msg")
                if user != "admin" and c3.button("Elimina", key=f"del_{user}"):
                    del db[user]
                    salva_db(db)
                    st.rerun()

    # PAGINA: MEMORIA (CATALOGO)
    elif st.session_state.pagina_attiva == "memoria":
        st.title("📚 Catalogo delle Memorie")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    st.markdown(f"""<div class="mem-card"><strong>📌 {k}</strong><br>{v}</div>""", unsafe_allow_html=True)
            else: st.info("Il tuo catalogo è vuoto. Inizia a chattare per salvare concetti.")
        except Exception as e: st.error(f"Errore caricamento: {e}")

    # PAGINA: IMPOSTAZIONI
    elif st.session_state.pagina_attiva == "settings":
        st.title("⚙️ Impostazioni")
        st.write("Gestisci i tuoi dati e le preferenze del sistema.")
        if st.button("🗑️ Svuota Cronologia Chat"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Cronologia eliminata!")

    # PAGINA: CHAT (DEFAULT)
    else:
        st.markdown("<h2 style='text-align: center;'>🧠 Brain Interface</h2>", unsafe_allow_html=True)
        
        # Area Messaggi
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        # Input
        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)

            try:
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                with st.chat_message("assistant"): st.write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                # Salvataggio persistente nel database
                db = carica_db()
                db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                salva_db(db)
            except Exception as e:
                st.error(f"Errore IA: {e}")
