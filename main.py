import streamlit as st
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import bcrypt, json, re, logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Cervello Contextual PRO", page_icon="🧠", layout="wide")

DEFAULT_ADMIN_PASS = st.secrets.get("default", {}).get("admin_password", "admin123_change_me")

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(20), unique=True, nullable=False)
    password_hash = sa.Column(sa.String(128), nullable=False)
    role = sa.Column(sa.String(10), default="user")
    history = sa.Column(sa.Text, default="[]")
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

engine = sa.create_engine("sqlite:///app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(User).filter_by(username="admin").first():
            admin_hash = bcrypt.hashpw(DEFAULT_ADMIN_PASS.encode(), bcrypt.gensalt()).decode()
            db.add(User(username="admin", password_hash=admin_hash, role="admin"))
            db.commit()

def get_user(username: str):
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if user:
            return {
                "id": user.id, "username": user.username, "password_hash": user.password_hash,
                "role": user.role, "history": json.loads(user.history)
            }
    return None

def create_user(username: str, password: str):
    if len(password) < 8: return False, "Password minimo 8 caratteri"
    if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username): return False, "Username non valido"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with SessionLocal() as db:
        try:
            db.add(User(username=username, password_hash=password_hash))
            db.commit()
            return True, "Account creato"
        except IntegrityError:
            return False, "Username già esistente"

def update_history(username: str, history: list):
    with SessionLocal() as db:
        db.query(User).filter_by(username=username).update({"history": json.dumps(history)})
        db.commit()

try:
    import cervello
except ImportError:
    class CervelloMock:
        def elabora_concetto(self, user, prompt): return f"Mock: '{prompt}'"
        def carica_memoria(self, user): return {"mem_1": "Dato esempio"}
    cervello = CervelloMock()

if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None
    st.session_state.role = 'user'
    st.session_state.chat_history = []
    st.session_state.pagina_attiva = 'chat'

init_db()

if not st.session_state.autenticato:
    st.title("🧠 Contextual Brain")
    t_log, t_reg = st.tabs(["Login", "Registrati"])

    with t_log:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ACCEDI"):
                user = get_user(u)
                if user and bcrypt.checkpw(p.encode(), user["password_hash"].encode()):
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.session_state.role = user["role"]
                    st.session_state.chat_history = user["history"]
                    st.rerun()
                else:
                    st.error("Credenziali errate")

    with t_reg:
        with st.form("register"):
            nu = st.text_input("Nuovo Username")
            np = st.text_input("Nuova Password", type="password")
            if st.form_submit_button("CREA ACCOUNT"):
                success, msg = create_user(nu, np)
                st.success(msg) if success else st.error(msg)

else:
    with st.sidebar:
        st.write(f"### 👋 {st.session_state.utente_attuale.upper()}")
        pagina = st.radio("Menu", ["Chat", "Memoria", "Impostazioni"])
        if st.session_state.role == "admin":
            if st.button("Admin"): pagina = "Admin"
        if st.button("Esci"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if pagina == "Admin" and st.session_state.role == "admin":
        st.title("Pannello Admin")
        with SessionLocal() as db:
            users = db.query(User).all()
            for u in users:
                st.write(f"{u.username} - {u.role}")

    elif pagina == "Impostazioni":
        st.title("Impostazioni")
        with st.form("cambio_pw"):
            old = st.text_input("Vecchia Password", type="password")
            new1 = st.text_input("Nuova Password", type="password")
            new2 = st.text_input("Conferma Nuova", type="password")
            if st.form_submit_button("Aggiorna"):
                with SessionLocal() as db:
                    u = db.query(User).filter_by(username=st.session_state.utente_attuale).first()
                    if not bcrypt.checkpw(old.encode(), u.password_hash.encode()):
                        st.error("Password vecchia errata")
                    elif new1!= new2:
                        st.error("Le password non coincidono")
                    elif len(new1) < 8:
                        st.error("Minimo 8 caratteri")
                    else:
                        u.password_hash = bcrypt.hashpw(new1.encode(), bcrypt.gensalt()).decode()
                        db.commit()
                        st.success("Password aggiornata")

    elif pagina == "Memoria":
        st.title("Archivio Memoria")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        for k, v in mem.items():
            with st.expander(k): st.write(v)

    else:
        st.title("Brain Chat")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        # NIENTE st.chat_input. Usiamo form normale che non rompe il DOM su mobile
        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_input("Scrivi...", key="chat_input")
            inviato = st.form_submit_button("Invia")
            if inviato and prompt:
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                risp = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": risp})
                update_history(st.session_state.utente_attuale, st.session_state.chat_history)
                st.rerun()
