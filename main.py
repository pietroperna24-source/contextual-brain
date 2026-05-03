import streamlit as st
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
import bcrypt, json, re, logging, smtplib, secrets, pyotp, qrcode
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from PIL import Image
import pandas as pd
from typing import Optional
from streamlit_limiter import rate_limit

# --- 0. LOGGING ---
log_handler = RotatingFileHandler('app.log', maxBytes=1_000_000, backupCount=3)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', handlers=[log_handler, logging.StreamHandler()])
logger = logging.getLogger(__name__)

# --- 1. CONFIG ---
st.set_page_config(page_title="Cervello Contextual PRO", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
DEFAULT_ADMIN_PASS = st.secrets.get("default", {}).get("admin_password", "admin123_change_me")

# --- 2. DB MODELS ---
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.String(20), unique=True, nullable=False, index=True)
    password_hash = sa.Column(sa.String(128), nullable=False)
    email = sa.Column(sa.String(100), unique=True, nullable=True)
    role = sa.Column(sa.String(10), default="user")
    history = sa.Column(sa.Text, default="[]")
    is_banned = sa.Column(sa.Boolean, default=False)
    banned_until = sa.Column(sa.DateTime, nullable=True)
    totp_secret = sa.Column(sa.String(32), nullable=True)
    reset_token = sa.Column(sa.String(64), nullable=True)
    reset_token_expires = sa.Column(sa.DateTime, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    last_login = sa.Column(sa.DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = sa.Column(sa.Integer, primary_key=True)
    timestamp = sa.Column(sa.DateTime, default=datetime.utcnow)
    username = sa.Column(sa.String(20))
    action = sa.Column(sa.String(100))
    details = sa.Column(sa.Text)

engine = sa.create_engine("sqlite:///app.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(User).filter_by(username="admin").first():
            admin_hash = bcrypt.hashpw(DEFAULT_ADMIN_PASS.encode(), bcrypt.gensalt()).decode()
            db.add(User(username="admin", password_hash=admin_hash, role="admin"))
            db.commit()
            log_action("system", "init_db", "Admin creato")

def log_action(username: str, action: str, details: str = ""):
    with SessionLocal() as db:
        db.add(AuditLog(username=username, action=action, details=details))
        db.commit()
    logger.info(f"{username} - {action} - {details}")

# --- 3. UTILS ---
def password_valida(password: str) -> tuple[bool, str]:
    if len(password) < 8: return False, "Minimo 8 caratteri"
    if not re.search(r"[A-Z]", password): return False, "Almeno 1 maiuscola"
    if not re.search(r"[a-z]", password): return False, "Almeno 1 minuscola"
    if not re.search(r"[0-9]", password): return False, "Almeno 1 numero"
    return True, "OK"

def username_valido(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_]{3,20}$', username))

def send_email(to_email: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg['From'] = st.secrets["email"]["sender"]
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(st.secrets["email"]["smtp_server"], st.secrets["email"]["smtp_port"])
        server.starttls()
        server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Errore invio email: {e}")
        return False

# --- 4. SERVIZI DB ---
@st.cache_data(ttl=10)
def get_user(username: str) -> Optional[dict]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if user:
            return {c.name: getattr(user, c.name) for c in user.__table__.columns}
    return None

def create_user(username: str, password: str, email: str) -> tuple[bool, str]:
    valid, msg = password_valida(password)
    if not valid: return False, msg
    if not username_valido(username): return False, "Username non valido"
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Email non valida"

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with SessionLocal() as db:
        try:
            db.add(User(username=username, password_hash=password_hash, email=email))
            db.commit()
            get_user.clear()
            log_action(username, "register", f"Email: {email}")
            return True, "Account creato"
        except IntegrityError:
            return False, "Username o email già esistente"

def generate_reset_token(username: str) -> Optional[str]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(username=username).first()
        if not user or not user.email: return None
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        link = f"https://TUO-APP-URL/?token={token}" # Cambia con il tuo URL Streamlit
        body = f"Ciao {username},\nClicca per resettare la password: {link}\nScade tra 1 ora."
        if send_email(user.email, "Reset Password Cervello", body):
            log_action(username, "reset_request", "Email inviata")
            return token
    return None

def reset_password_with_token(token: str, new_password: str) -> tuple[bool, str]:
    valid, msg = password_valida(new_password)
    if not valid: return False, msg
    with SessionLocal() as db:
        user = db.query(User).filter_by(reset_token=token).first()
        if not user or user.reset_token_expires < datetime.utcnow():
            return False, "Token non valido o scaduto"
        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        get_user.clear()
        log_action(user.username, "reset_password", "Via token")
        return True, "Password resettata"

def setup_2fa(username: str) -> str:
    secret = pyotp.random_base32()
    with SessionLocal() as db:
        db.query(User).filter_by(username=username).update({"totp_secret": secret})
        db.commit()
    get_user.clear()
    return secret

def verify_2fa(username: str, code: str) -> bool:
    user = get_user(username)
    if not user or not user.get("totp_secret"): return False
    totp = pyotp.TOTP(user["totp_secret"])
    return totp.verify(code)

def update_history(username: str, history: list):
    with SessionLocal() as db:
        db.query(User).filter_by(username=username).update({"history": json.dumps(history)})
        db.commit()
    get_user.clear()

# --- 5. CERVELLO MOCK ---
try:
    import cervello
except ImportError:
    class CervelloMock:
        def elabora_concetto(self, user, prompt, files=None):
            return f"Mock: '{prompt}'. File ricevuti: {len(files) if files else 0}"
        def carica_memoria(self, user): return {f"mem_{i}": f"Dato {i}" for i in range(25)}
    cervello = CervelloMock()

# --- 6. SESSION STATE + AUTO LOGOUT ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False, 'utente_attuale': None, 'role': 'user',
        'chat_history': [], 'pagina_attiva': 'chat', 'theme': 'light',
        '2fa_passed': False, 'last_activity': datetime.utcnow()
    })

# Auto-logout dopo 30 min inattività
if st.session_state.autenticato:
    if datetime.utcnow() - st.session_state.last_activity > timedelta(minutes=30):
        st.session_state.clear()
        st.rerun()
    st.session_state.last_activity = datetime.utcnow()

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

if st.session_state.theme == 'dark':
    st.markdown("<style>.stApp { background-color: #0E1117; color: #FAFAFA; }</style>", unsafe_allow_html=True)

init_db()

# --- 7. RESET PASSWORD VIA TOKEN URL ---
query_params = st.query_params
if "token" in query_params:
    st.title("🔑 Reset Password")
    token = query_params["token"]
    with st.form("reset_form"):
        new_pw = st.text_input("Nuova Password", type="password")
        new_pw2 = st.text_input("Conferma Password", type="password")
        if st.form_submit_button("Resetta"):
            if new_pw!= new_pw2: st.error("Le password non coincidono")
            else:
                ok, msg = reset_password_with_token(token, new_pw)
                st.success(msg) if ok else st.error(msg)
                if ok: st.query_params.clear()
    st.stop()

# --- 8. LOGIN ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align:center'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t_log, t_reg, t_reset = st.tabs(["🔐 Login", "📝 Registrati", "🔄 Recupera Password"])

        with t_log:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("ACCEDI", use_container_width=True):
                    if rate_limit(limit=5, period=60):
                        user = get_user(u)
                        if user and bcrypt.checkpw(p.encode(), user["password_hash"].encode()):
                            if user["is_banned"] and user["banned_until"] > datetime.utcnow():
                                st.error(f"Account bannato fino al {user['banned_until']}")
                            else:
                                st.session_state.utente_attuale = u
                                st.session_state.role = user["role"]
                                if user["totp_secret"]: # Richiedi 2FA
                                    st.session_state.need_2fa = True
                                    st.rerun()
                                else:
                                    st.session_state.autenticato = True
                                    st.session_state.chat_history = json.loads(user["history"])
                                    with SessionLocal() as db:
                                        db.query(User).filter_by(id=user["id"]).update({"last_login": datetime.utcnow()})
                                        db.commit()
                                    log_action(u, "login", "Success")
                                    st.rerun()
                        else:
                            st.error("Credenziali errate")
                            log_action(u, "login", "Failed")

        # 2FA SCREEN
        if st.session_state.get("need_2fa"):
            st.info("Inserisci il codice da Google Authenticator")
            code = st.text_input("Codice 2FA", max_chars=6)
            if st.button("Verifica"):
                if verify_2fa(st.session_state.utente_attuale, code):
                    st.session_state.autenticato = True
                    st.session_state['2fa_passed'] = True
                    user = get_user(st.session_state.utente_attuale)
                    st.session_state.chat_history = json.loads(user["history"])
                    del st.session_state.need_2fa
                    log_action(st.session_state.utente_attuale, "2fa", "Success")
                    st.rerun()
                else:
                    st.error("Codice errato")

        with t_reg:
            with st.form("register"):
                nu = st.text_input("Nuovo Username")
                em = st.text_input("Email")
                np = st.text_input("Nuova Password", type="password")
                if st.form_submit_button("CREA ACCOUNT", use_container_width=True):
                    success, msg = create_user(nu, np, em)
                    st.success(msg) if success else st.error(msg)

        with t_reset:
            ru = st.text_input("Username per reset")
            if st.button("Invia Email Reset"):
                if generate_reset_token(ru):
                    st.success("Se l'email esiste, ti abbiamo inviato il link")
                else:
                    st.success("Se l'email esiste, ti abbiamo inviato il link") # Non dire se esiste o no

else:
    # --- 9. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Ruolo: {st.session_state.role}")
        st.button("🌓 Cambia Tema", on_click=toggle_theme, use_container_width=True)
        st.divider()
        nav = {"💬 Chat": "chat", "🧠 Memoria": "memoria", "⚙️ Impostazioni": "settings", "📊 Log": "logs"}
        if st.session_state.role == "admin": nav["🛡️ Admin"] = "admin"
        for label, page in nav.items():
            if st.button(label, use_container_width=True):
                st.session_state.pagina_attiva = page; st.rerun()
        st.divider()
        if st.button("🚪 Esci", type="primary", use_container_width=True):
            log_action(st.session_state.utente_attuale, "logout", "")
            st.session_state.clear(); st.rerun()

    # --- 10. PAGINE ---
    page = st.session_state.pagina_attiva

    # ADMIN
    if page == "admin" and st.session_state.role == "admin":
        st.title("🛡️ Pannello Admin")
        with SessionLocal() as db:
            users = db.query(User).all()
            df = pd.DataFrame([{"Username": u.username, "Ruolo": u.role, "Email": u.email, "Bannato": u.is_banned, "2FA": bool(u.totp_secret)} for u in users])
        st.dataframe(df, use_container_width=True)

        st.subheader("Gestione Utente")
        target = st.selectbox("Utente", [u.username for u in users if u.username!= "admin"])
        c1, c2, c3 = st.columns(3)
        if c1.button("Reset Password"):
            new_pass = f"Temp{secrets.token_hex(4)}!"
            with SessionLocal() as db:
                db.query(User).filter_by(username=target).update({"password_hash": bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()})
                db.commit()
            st.success(f"Nuova password per {target}: `{new_pass}`")
            log_action("admin", "admin_reset_pw", target)
        if c2.button("Banna 7 giorni"):
            with SessionLocal() as db:
                db.query(User).filter_by(username=target).update({"is_banned": True, "banned_until": datetime.utcnow() + timedelta(days=7)})
                db.commit()
            st.success(f"{target} bannato"); get_user.clear()
        if c3.button("Rimuovi 2FA"):
            with SessionLocal() as db:
                db.query(User).filter_by(username=target).update({"totp_secret": None})
                db.commit()
            st.success(f"2FA rimossa per {target}"); get_user.clear()

    # LOGS
    elif page == "logs":
        st.title("📊 Audit Log")
        with SessionLocal() as db:
            logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200).all()
            df_logs = pd.DataFrame([{"Data": l.timestamp, "Utente": l.username, "Azione": l.action, "Dettagli": l.details} for l in logs])
        st.dataframe(df_logs, use_container_width=True)

    # IMPOSTAZIONI con 2FA
    elif page == "settings":
        st.title("⚙️ Impostazioni")
        user = get_user(st.session_state.utente_attuale)

        st.subheader("🔐 Sicurezza - 2FA")
        if not user["totp_secret"]:
            if st.button("Abilita Google Authenticator"):
                secret = setup_2fa(st.session_state.utente_attuale)
                uri = pyotp.totp.TOTP(secret).provisioning_uri(name=st.session_state.utente_attuale, issuer_name="CervelloApp")
                img = qrcode.make(uri)
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.image(buf, caption="Scansiona con Google Authenticator")
                st.code(secret)
                st.warning("Salva questo codice segreto. Dopo il refresh non lo vedrai più.")
                log_action(st.session_state.utente_attuale, "2fa_enable", "")
        else:
            st.success("2FA Attiva ✅")
            if st.button("Disabilita 2FA", type="primary"):
                with SessionLocal() as db:
                    db.query(User).filter_by(username=st.session_state.utente_attuale).update({"totp_secret": None})
                    db.commit()
                st.success("2FA disabilitata"); get_user.clear(); st.rerun()

        st.divider()
        with st.form("cambio_pw"):
            st.subheader("🔑 Cambia Password")
            old = st.text_input("Vecchia Password", type="password")
            new1 = st.text_input("Nuova Password", type="password")
            new2 = st.text_input("Conferma Nuova", type="password")
            if st.form_submit_button("Aggiorna"):
                with SessionLocal() as db:
                    u = db.query(User).filter_by(username=st.session_state.utente_attuale).first()
                    if not bcrypt.checkpw(old.encode(), u.password_hash.encode()):
                        st.error("Password vecchia errata")
                    elif new1!= new2: st.error("Le password non coincidono")
                    else:
                        valid, msg = password_valida(new1)
                        if not valid: st.error(msg)
                        else:
                            u.password_hash = bcrypt.hashpw(new1.encode(), bcrypt.gensalt()).decode()
                            db.commit()
                            st.success("Password aggiornata"); get_user.clear()
                            log_action(st.session_state.utente_attuale, "change_pw", "Self")

    # MEMORIA
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
        else: st.info("Nessuna memoria.")

    # CHAT con UPLOAD
    else:
        st.title("🧠 Brain Chat")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])

        uploaded_files = st.file_uploader("Allega PDF o immagini", accept_multiple_files=True, type=['pdf','png','jpg','jpeg'])
        if prompt := st.chat_input("Scrivi..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            try:
                with st.spinner("Penso..."):
                    risp = cervello.elabora_concetto(st.session_state.utente_attuale, prompt, files=uploaded_files)
                with st.chat_message("assistant"): st.write(risp)
                st.session_state.chat_history.append({"role": "assistant", "content": risp})
                update_history(st.session_state.utente_attuale, st.session_state.chat_history)
                log_action(st.session_state.utente_attuale, "chat", f"Msg len: {len(prompt)}")
            except Exception as e:
                st.error("Errore del cervello")
                logger.exception("Errore elaborazione")
