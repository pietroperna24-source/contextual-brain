import streamlit as st
import sqlite3
import json
import re
import logging
import bcrypt
from pathlib import Path
from contextlib import contextmanager

# --- 0. SETUP LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual PRO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM ---
st.markdown("""
    <style>
       .stApp { background-color: #F8F9FA; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; }
       .main-title { font-size: 2.2rem; font-weight: 800; color: #2D3436; text-align: center; }
       .memoria-item {
            padding: 8px; border-radius: 5px; background: #F1F2F6;
            margin-bottom: 5px; font-size: 0.85rem; border-left: 3px solid #6C5CE7;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. MODULO CERVELLO MOCK ---
# Rimuovi questo blocco quando hai il vero modulo cervello.py
try:
    import cervello
except ImportError:
    class CervelloMock:
        def elabora_concetto(self, user, prompt):
            return f"Mock: ho ricevuto '{prompt}' da {user}"

        def carica_memoria(self, user):
            # Sanitizza il nome utente per evitare path traversal
            safe_user = re.sub(r'[^a-zA-Z0-9_]', '', user)
            return {"esempio_1": f"Memoria finta per {safe_user}", "esempio_2": "Altra memoria"}
    cervello = CervelloMock()
    logging.warning("Modulo 'cervello' non trovato. Uso mock.")

# --- 4. DATABASE SQLITE ---
DB_PATH = "app.db"

@contextmanager
def get_db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()

def init_db():
    with get_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                history TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Crea admin di default se non esiste
        cur = con.execute("SELECT 1 FROM users WHERE username = 'admin'")
        if not cur.fetchone():
            admin_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            con.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                ("admin", admin_hash, "admin")
            )
        con.commit()

@st.cache_data(ttl=5) # Cache 5 secondi per evitare troppe letture
def get_user(username: str):
    with get_db() as con:
        cur = con.execute("SELECT * FROM users WHERE username =?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None

def create_user(username: str, password: str) -> bool:
    if get_user(username):
        return False
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with get_db() as con:
        con.execute(
            "INSERT INTO users (username, password_hash) VALUES (?,?)",
            (username, password_hash)
        )
        con.commit()
    get_user.clear() # Invalida cache
    return True

def update_history(username: str, history: list):
    with get_db() as con:
        con.execute(
            "UPDATE users SET history =? WHERE username =?",
            (json.dumps(history), username)
        )
        con.commit()
    get_user.clear()

def delete_user(username: str):
    with get_db() as con:
        con.execute("DELETE FROM users WHERE username =?", (username,))
        con.commit()
    get_user.clear()

def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    user_data = get_user(username)
    if not user_data:
        return False, "Utente non trovato"
    
    if not bcrypt.checkpw(old_password.encode(), user_data["password_hash"].encode()):
        return False, "Password attuale errata"
    
    if not password_valida(new_password):
        return False, "La nuova password deve avere almeno 8 caratteri"
    
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_db() as con:
        con.execute(
            "UPDATE users SET password_hash =? WHERE username =?",
            (new_hash, username)
        )
        con.commit()
    get_user.clear()
    return True, "Password aggiornata con successo"
    
def get_all_users():
    with get_db() as con:
        cur = con.execute("SELECT username, role, history, created_at FROM users ORDER BY created_at")
        return [dict(row) for row in cur.fetchall()]

# --- 5. VALIDAZIONE ---
def username_valido(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def password_valida(password: str) -> bool:
    return len(password) >= 8

# --- 6. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': [],
        'pagina_attiva': 'chat',
        'tentativi_login': 0
    })

# --- 7. INIT DB AL PRIMO AVVIO ---
init_db()

# --- 8. LOGICA ACCESSO ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Login", "📝 Registrati"])

        with t_log:
            u = st.text_input("Username", key="login_user")
            p = st.text_input("Password", type="password", key="login_pass")

            if st.button("ACCEDI", use_container_width=True):
                if st.session_state.tentativi_login >= 5:
                    st.error("Troppi tentativi. Riprova tra 30 secondi.")
                else:
                    user_data = get_user(u)
                    if user_data and bcrypt.checkpw(p.encode(), user_data["password_hash"].encode()):
                        st.session_state.update({
                            'autenticato': True,
                            'utente_attuale': u,
                            'role': user_data["role"],
                            'chat_history': json.loads(user_data["history"]),
                            'tentativi_login': 0
                        })
                        logging.info(f"Login riuscito: {u}")
                        st.rerun()
                    else:
                        st.session_state.tentativi_login += 1
                        st.error("Credenziali errate")
                        logging.warning(f"Login fallito per: {u}")

        with t_reg:
            nu = st.text_input("Nuovo Username", key="reg_user")
            np = st.text_input("Nuova Password", type="password", key="reg_pass")

            if st.button("CREA ACCOUNT", use_container_width=True):
                if not username_valido(nu):
                    st.error("Username: solo lettere, numeri, _. 3-20 caratteri")
                elif not password_valida(np):
                    st.error("Password minimo 8 caratteri")
                elif create_user(nu, np):
                    st.success("Account creato! Vai su Login.")
                    logging.info(f"Nuovo utente registrato: {nu}")
                else:
                    st.error("Username già esistente")

else:
    # --- 9. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Profilo: {st.session_state.role}")
        st.write("---")

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
            logging.info(f"Logout: {st.session_state.utente_attuale}")
            st.session_state.clear()
            st.rerun()

    # --- 10. PAGINE ---

    # PAGINA: ADMIN
    if st.session_state.pagina_attiva == "admin" and st.session_state.role == "admin":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
        st.title("🛡️ Gestione Sistema")
        users = get_all_users()
        st.write(f"### Utenti Attivi: {len(users)}")
        for user in users:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            col1.write(f"👤 **{user['username']}** ({user['role']})")
            history_len = len(json.loads(user['history']))
            col2.write(f"💬 {history_len} msg")
            col3.write(f"📅 {user['created_at'][:10]}")
            if user['username']!= "admin" and col4.button("Elimina", key=f"del_{user['username']}"):
                delete_user(user['username'])
                st.success(f"Utente {user['username']} eliminato")
                st.rerun()

    # PAGINA: MEMORIA
    elif st.session_state.pagina_attiva == "memoria":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
        st.title("📂 Archivio Memoria")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"):
                        st.write(v)
            else:
                st.info("Nessuna memoria trovata.")
        except Exception as e:
            st.error("Errore nel caricamento memoria.")
            logging.exception(f"Errore carica_memoria per {st.session_state.utente_attuale}")

    # PAGINA: IMPOSTAZIONI
    elif st.session_state.pagina_attiva == "settings":
        if st.button("⬅️ Indietro alla Chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
        st.title("⚙️ Impostazioni")
        st.warning("⚠️ Attenzione: questa azione è irreversibile")
        if st.button("🗑️ Svuota Cronologia Chat", type="primary"):
            st.session_state.chat_history = []
            update_history(st.session_state.utente_attuale, [])
            st.success("Cronologia cancellata!")

    # PAGINA: CHAT
    else:
        st.markdown(f"<h2 style='text-align: center;'>🧠 Brain Chat</h2>", unsafe_allow_html=True)

        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        if prompt := st.chat_input("Chiedi o memorizza..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            try:
                with st.spinner("Elaboro..."):
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                with st.chat_message("assistant"):
                    st.write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                update_history(st.session_state.utente_attuale, st.session_state.chat_history)
            except Exception as e:
                st.error(f"Errore: {e}")
                logging.exception(f"Errore elaborazione per {st.session_state.utente_attuale}")
