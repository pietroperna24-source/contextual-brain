import streamlit as st
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import bcrypt
import json
import re
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from typing import Optional
from streamlit_limiter import rate_limit

# --- 0. LOGGING SU FILE ---
log_handler = RotatingFileHandler('app.log', maxBytes=1_000_000, backupCount=3)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[log_handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- 1. CONFIGURAZIONE + SECRETS ---
st.set_page_config(
    page_title="Cervello Contextual PRO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Usa st.secrets per dati sensibili. Crea.streamlit/secrets.toml
# [default]
# admin_password = "cambia_questa_password_forte"
DEFAULT_ADMIN_PASS = st.secrets.get("default", {}).get("admin_password", "admin123_change_me")

# --- 2. DATABASE SQLALCHEMY ---
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(20), unique=True, nullable=False, index=True)
    password_hash = sa.Column(sa.String(128), nullable=False)
    role = sa.Column(sa.String(10), default="user")
    history = sa.Column(sa.Text, default="[]")
    is_banned = sa.Column(sa.Boolean, default=False)
    banned_until = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    last_login = sa.Column(sa.DateTime, nullable=True)

engine = sa.create_engine("sqlite:///app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(User).filter_by(username="admin").first():
            admin_hash = bcrypt.hashpw(DEFAULT_ADMIN_PASS.encode(), bcrypt.gensalt()).decode()
            db.add(User(username="admin", password_hash=admin_hash, role="admin"))
            db.commit()
            logger.info("Utente admin creato")

@st.cache_resource
def get_db_session() -> Session:
    return SessionLocal()

# --- 3. UTILS SICUREZZA ---
def password_valida(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Minimo 8 caratteri"
    if not re.search(r"[A-Z]", password):
        return False, "Almeno 1 maiuscola"
    if not re.search(r"[a-z]", password):
        return False, "Almeno 1 minuscola"
    if not re.search(r"[0-9]", password):
        return False, "Almeno 1 numero"
    return True, "OK"

def username_valido(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def check_ban(user: User) -> bool:
    if user.is_banned:
        if user.banned_until and user.banned_until > datetime.utcnow():
            return True
        else: # Ban scaduto
            user.is_banned = False
            user.banned_until = None
    return False

# --- 4. SERVIZI DB ---
@st.cache_data(ttl=10)
def get_user(username: str) -> Optional[dict]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if user:
            return {
                "id": user.id, "username": user.username, "password_hash": user.password_hash,
                "role": user.role, "history": json.loads(user.history), "is_banned": user.is_banned,
                "banned_until": user.banned_until, "created_at": user.created_at
            }
    return None

def create_user(username: str, password: str) -> tuple[bool, str]:
    valid, msg = password_valida(password)
    if not valid: return False, msg
    if not username_valido(username): return False, "Username non valido"

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with SessionLocal() as db:
        try:
            db.add(User(username=username, password_hash=password_hash))
            db.commit()
            get_user.clear()
            logger.info(f"Nuovo utente: {username}")
            return True, "Account creato"
        except IntegrityError:
            return False, "Username già esistente"

def update_user_password(username: str, new_password: str, by_admin: bool = False, old_password: str = None) -> tuple[bool, str]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if not user: return False, "Utente non trovato"

        if not by_admin:
            if not bcrypt.checkpw(old_password.encode(), user.password_hash.encode()):
                return False, "Password attuale errata"

        valid, msg = password_valida(new_password)
        if not valid: return False, msg

        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        db.commit()
        get_user.clear()
        logger.info(f"Password aggiornata per {username}. By admin: {by_admin}")
        return True, "Password aggiornata"

def update_history(username: str, history: list):
    with SessionLocal() as db:
        db.query(User).filter_by(username=username).update({"history": json.dumps(history)})
        db.commit()
    get_user.clear()

def admin_update_user(username: str, role: str = None, ban_days: int = 0):
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if not user: return
        if role: user.role = role
        if ban_days > 0:
            user.is_banned = True
            user.banned_until = datetime.utcnow() + timedelta(days=ban_days)
        elif ban_days == -1: # Unban
            user.is_banned = False
            user.banned_until = None
        db.commit()
    get_user.clear()

# --- 5. CERVELLO MOCK ---
try:
    import cervello
except ImportError:
    class CervelloMock:
        def elabora_concetto(self, user, prompt): return f"Mock: '{prompt}'"
        def carica_memoria(self, user): return {f"mem_{i}": f"Dato {i}" for i in range(25)}
    cervello = CervelloMock()

# --- 6. SESSION STATE + TEMA ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False, 'utente_attuale': None, 'role': 'user',
        'chat_history': [], 'pagina_attiva': 'chat', 'theme': 'light'
    })

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# Applica tema
if st.session_state.theme == 'dark':
    st.markdown("<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>", unsafe_allow_html=True)

init_db()

# --- 7. LOGIN CON RATE LIMIT ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align:center'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Login", "📝 Registrati"])

        with t_log:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("ACCEDI", use_container_width=True):
                    # Rate limit: 5 tentativi al minuto per sessione
                    if rate_limit(limit=5, period=60):
                        user = get_user(u)
                        if user and bcrypt.checkpw(p.encode(), user["password_hash"].encode()):
                            if check_ban(db_user := SessionLocal().query(User).get(user["id"])):
                                st.error(f"Account bannato fino al {user['banned_until']}")
                            else:
                                with SessionLocal() as db:
                                    db.query(User).filter_by(id=user["id"]).update({"last_login": datetime.utcnow()})
                                    db.commit()
                                st.session_state.update({
                                    'autenticato': True, 'utente_attuale': u,
                                    'role': user["role"], 'chat_history': user["history"]
                                })
                                st.rerun()
                        else:
                            st.error("Credenziali errate")

        with t_reg:
            with st.form("register"):
                nu = st.text_input("Nuovo Username")
                np = st.text_input("Nuova Password", type="password", help="8+ char, 1 maiusc, 1 min, 1 numero")
                if st.form_submit_button("CREA ACCOUNT", use_container_width=True):
                    success, msg = create_user(nu, np)
                    st.success(msg) if success else st.error(msg)

else:
    # --- 8. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Ruolo: {st.session_state.role}")
        st.button("🌓 Cambia Tema", on_click=toggle_theme, use_container_width=True)
        st.divider()

        nav = {
            "💬 Chat": "chat", "🧠 Memoria": "memoria", "⚙️ Impostazioni": "settings"
        }
        if st.session_state.role == "admin": nav["🛡️ Admin"] = "admin"

        for label, page in nav.items():
            if st.button(label, use_container_width=True):
                st.session_state.pagina_attiva = page
                st.rerun()

        st.divider()
        if st.button("🚪 Esci", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- 9. PAGINE ---
    page = st.session_state.pagina_attiva

    # ADMIN
    if page == "admin" and st.session_state.role == "admin":
        st.title("🛡️ Pannello Admin")

        with SessionLocal() as db:
            users = db.query(User).all()
            df = pd.DataFrame([{
                "Username": u.username, "Ruolo": u.role, "Msg": len(json.loads(u.history)),
                "Creato": u.created_at.strftime("%Y-%m-%d"), "Bannato": u.is_banned,
                "Ultimo Login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "Mai"
            } for u in users])

        st.dataframe(df, use_container_width=True)

        st.subheader("Gestione Utente")
        col1, col2, col3 = st.columns(3)
        target_user = col1.selectbox("Utente", [u.username for u in users if u.username!= "admin"])
        new_role = col2.selectbox("Nuovo Ruolo", ["user", "admin"])
        ban_days = col3.number_input("Ban giorni (0=no, -1=unban)", value=0)

        c1, c2, c3 = st.columns(3)
        if c1.button("Aggiorna Ruolo/Ban"):
            admin_update_user(target_user, role=new_role, ban_days=ban_days)
            st.success(f"{target_user} aggiornato"); st.rerun()
        if c2.button("Reset Password"):
            new_pass = "Temp1234!" # Genera casuale in prod
            update_user_password(target_user, new_pass, by_admin=True)
            st.success(f"Password di {target_user} resettata a: `{new_pass}`")

        with st.expander("⚠️ Zona Pericolo"):
            if st.button(f"ELIMINA {target_user}", type="primary"):
                with SessionLocal() as db:
                    db.query(User).filter_by(username=target_user).delete()
                    db.commit()
                st.success(f"{target_user} eliminato"); st.rerun()

    # IMPOSTAZIONI
    elif page == "settings":
        st.title("⚙️ Impostazioni")
        with st.form("cambio_pw"):
            st.subheader("🔑 Cambia Password")
            old = st.text_input("Vecchia Password", type="password")
            new1 = st.text_input("Nuova Password", type="password")
            new2 = st.text_input("Conferma Nuova", type="password")
            if st.form_submit_button("Aggiorna"):
                if new1!= new2: st.error("Le password non coincidono")
                else:
                    ok, msg = update_user_password(st.session_state.utente_attuale, new1, old_password=old)
                    st.success(msg) if ok else st.error(msg)

        st.divider()
        st.subheader("📤 Esporta Chat")
        chat_export = "\n\n".join([f"**{m['role']}**: {m['content']}" for m in st.session_state.chat_history])
        st.download_button("Scarica.md", chat_export, f"chat_{st.session_state.utente_attuale}.md")

        with st.expander("🗑️ Elimina Dati"):
            if st.button("Svuota Cronologia", type="primary"):
                st.session_state.chat_history = []
                update_history(st.session_state.utente_attuale, [])
                st.success("Fatto"); st.rerun()

    # MEMORIA CON PAGINAZIONE
    elif page == "memoria":
        st.title("📂 Archivio Memoria")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            items = list(mem.items())
            page_size = 10
            total_pages = (len(items) - 1) // page_size + 1
            page_num = st.number_input("Pagina", 1, total_pages, 1)
            start = (page_num - 1) * page_size
            for k, v in items[start:start+page_size]:
                with st.expander(f"📌 {k}"): st.write(v)
        else:
            st.info("Nessuna memoria.")

    # CHAT
    else:
        st.title("🧠 Brain Chat")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        if prompt := st.chat_input("Scrivi..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            try:
                with st.spinner("Penso..."):
                    risp = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                with st.chat_message("assistant"): st.write(risp)
                st.session_state.chat_history.append({"role": "assistant", "content": risp})
                update_history(st.session_state.utente_attuale, st.session_state.chat_history)
            except Exception as e:
                st.error("Errore del cervello")
                logger.exception("Errore elaborazione")
