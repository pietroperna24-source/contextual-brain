import streamlit as st
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import bcrypt, json, re, logging
from datetime import datetime, timedelta
from typing import Optional
import cervello

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Cervello Contextual PRO", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
DEFAULT_ADMIN_PASS = st.secrets.get("default", {}).get("admin_password", "admin123_change_me")

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

def password_valida(password: str) -> tuple[bool, str]:
    if len(password) < 8: return False, "Minimo 8 caratteri"
    if not re.search(r"[A-Z]", password): return False, "Almeno 1 maiuscola"
    if not re.search(r"[a-z]", password): return False, "Almeno 1 minuscola"
    if not re.search(r"[0-9]", password): return False, "Almeno 1 numero"
    return True, "OK"

def username_valido(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def get_user(username: str) -> Optional[dict]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role,
                "history": json.loads(user.history) if user.history else [],
                "is_banned": user.is_banned,
                "banned_until": user.banned_until
            }
    return None

def create_user(username: str, password: str) -> tuple[bool, str]:
    valid, msg = password_valida(password)
    if not valid: return False, msg
    if not username_valido(username): return False, "Username non valido: 3-20 caratteri, solo lettere/numeri/_"

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with SessionLocal() as db:
        try:
            db.add(User(username=username, password_hash=password_hash))
            db.commit()
            logger.info(f"Nuovo utente: {username}")
            return True, "Account creato"
        except IntegrityError:
            return False, "Username già esistente"

def update_history(username: str, history: list):
    with SessionLocal() as db:
        db.query(User).filter_by(username=username).update({"history": json.dumps(history)})
        db.commit()

if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': [],
        'pagina_attiva': 'chat'
    })

init_db()

if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align:center'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t_log, t_reg = st.tabs(["🔐 Login", "📝 Registrati"])

        with t_log:
            with st.form("login", clear_on_submit=True):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                submitted = st.form_submit_button("ACCEDI", use_container_width=True)
                if submitted:
                    user = get_user(u)
                    if user and bcrypt.checkpw(p.encode(), user["password_hash"].encode()):
                        if user["is_banned"] and user["banned_until"] and user["banned_until"] > datetime.utcnow():
                            st.error(f"Account bannato fino al {user['banned_until'].strftime('%d/%m/%Y %H:%M')}")
                        else:
                            st.session_state.autenticato = True
                            st.session_state.utente_attuale = u
                            st.session_state.role = user["role"]
                            st.session_state.chat_history = user["history"]
                            with SessionLocal() as db:
                                db.query(User).filter_by(id=user["id"]).update({"last_login": datetime.utcnow()})
                                db.commit()
                            st.rerun()
                    else:
                        st.error("Credenziali errate")

        with t_reg:
            with st.form("register", clear_on_submit=True):
                nu = st.text_input("Nuovo Username")
                np = st.text_input("Nuova Password", type="password", help="8+ char, 1 maiusc, 1 min, 1 numero")
                submitted = st.form_submit_button("CREA ACCOUNT", use_container_width=True)
                if submitted:
                    success, msg = create_user(nu, np)
                    st.success(msg) if success else st.error(msg)
else:
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Ruolo: {st.session_state.role}")
        st.divider()

        if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
            st.session_state.pagina_attiva = "chat"
            st.rerun()
        if st.button("🧠 Memoria", use_container_width=True, key="nav_memoria"):
            st.session_state.pagina_attiva = "memoria"
            st.rerun()
        if st.button("⚙️ Impostazioni", use_container_width=True, key="nav_settings"):
            st.session_state.pagina_attiva = "settings"
            st.rerun()
        if st.session_state.role == "admin":
            if st.button("🛡️ Admin", use_container_width=True, key="nav_admin"):
                st.session_state.pagina_attiva = "admin"
                st.rerun()

        st.divider()
        if st.button("🚪 Esci", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    page = st.session_state.pagina_attiva

    if page == "admin" and st.session_state.role == "admin":
        st.title("🛡️ Pannello Admin")
        with SessionLocal() as db:
            users = db.query(User).all()
            for u in users:
                col1, col2, col3 = st.columns([3,2,2])
                col1.write(f"**{u.username}** - {u.role}")
                col2.write("Bannato" if u.is_banned else "Attivo")
                if u.username!= "admin":
                    if col3.button("Banna 7gg", key=f"ban_{u.id}"):
                        db.query(User).filter_by(id=u.id).update({
                            "is_banned": True,
                            "banned_until": datetime.utcnow() + timedelta(days=7)
                        })
                        db.commit()
                        st.rerun()

    elif page == "settings":
        st.title("⚙️ Impostazioni")
        with st.form("cambio_pw", clear_on_submit=True):
            st.subheader("🔑 Cambia Password")
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
                    else:
                        valid, msg = password_valida(new1)
                        if not valid:
                            st.error(msg)
                        else:
                            u.password_hash = bcrypt.hashpw(new1.encode(), bcrypt.gensalt()).decode()
                            db.commit()
                            st.success("Password aggiornata")

    elif page == "memoria":
        st.title("📂 Archivio Memoria")
        memoria_key = f"memoria_{st.session_state.utente_attuale}"
        memoria_corrente = st.session_state.get(memoria_key, {})
        if memoria_corrente:
            for k, v in memoria_corrente.items():
                with st.expander(f"📌 {k}"):
                    st.write(v)
        else:
            st.info("Nessuna memoria salvata. Chiedi al cervello di ricordare qualcosa in chat.")

        if st.button("Svuota Memoria"):
            st.session_state[memoria_key] = {}
            st.rerun()

    else:
        st.title("🧠 Brain Chat")

        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        with st.form("chat_form", clear_on_submit=True):
            prompt = st.text_input("Scrivi...", key="chat_input", placeholder="Es: Ricorda che il mio colore preferito è blu")
            inviato = st.form_submit_button("Invia")

            if inviato and prompt:
                st.session_state.chat_history.append({"role": "user", "content": prompt})

                memoria_key = f"memoria_{st.session_state.utente_attuale}"
                memoria_corrente = st.session_state.get(memoria_key, {})

                with st.spinner("Penso..."):
                    risp = cervello.elabora_concetto(st.session_state.utente_attuale, prompt, memoria_corrente)

                if "SAVE|" in risp:
                    parti = risp.split("|")
                    if len(parti) >= 3:
                        chiave = parti[1].strip()
                        valore = parti[2].strip()
                        memoria_corrente[chiave] = valore
                        st.session_state[memoria_key] = memoria_corrente
                        risp = f"Ho memorizzato: **{chiave}** = {valore}"

                st.session_state.chat_history.append({"role": "assistant", "content": risp})
                update_history(st.session_state.utente_attuale, st.session_state.chat_history)
                st.rerun()
