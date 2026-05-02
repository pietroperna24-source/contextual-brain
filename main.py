import streamlit as st
import json
import os
import streamlit.components.v1 as components

# Prova a importare il modulo cervello
try:
    import cervello
except ImportError:
    cervello = None

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual PRO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"  # FORZA L'APERTURA DELLA TENDINA
)

# --- 2. UI ENGINE & CSS ---
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
        /* Sfondo e Sidebar */
        .stApp { background-color: #F8F9FB; }
        [data-testid="stSidebar"] { 
            background-color: #FFFFFF !important; 
            border-right: 1px solid #EAEAEA;
            min-width: 300px !important;
        }
        
        /* Bottoni */
        .stButton>button {
            border-radius: 10px;
            font-weight: 600;
            height: 3em;
            width: 100%;
        }

        /* Card per Memoria */
        .mem-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #6C5CE7;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. DATABASE ---
DB_FILE = "utenti.json"

def carica_db():
    if not os.path.exists(DB_FILE):
        db = {"admin": {"pass": "admin123", "history": [], "role": "admin"}}
        with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)
        return db
    with open(DB_FILE, "r") as f: return json.load(f)

def salva_db(db):
    with open(DB_FILE, "w") as f: json.dump(db, f, indent=4)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente': None,
        'ruolo': 'user',
        'history': [],
        'pagina': 'chat'
    })

# --- 5. SCHERMATA LOGIN ---
if not st.session_state.autenticato:
    _, col_c, _ = st.columns([1, 1.5, 1])
    with col_c:
        st.write("##")
        st.markdown("<h1 style='text-align: center;'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDI"):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True,
                        'utente': u,
                        'ruolo': db[u].get("role", "user"),
                        'history': db[u].get("history", [])
                    })
                    st.rerun()
                else: st.error("Credenziali errate")

        with t2:
            nu = st.text_input("Nuovo User")
            np = st.text_input("Nuova Pass", type="password")
            if st.button("CREA ACCOUNT"):
                db = carica_db()
                if nu and nu not in db:
                    db[nu] = {"pass": np, "history": [], "role": "user"}
                    salva_db(db)
                    st.success("Account creato!")

else:
    # --- 6. SIDEBAR (LA TUA TENDINA) ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente.upper()}")
        st.caption(f"Ruolo: {st.session_state.ruolo}")
        st.write("---")
        
        # Navigazione
        if st.button("💬 Chat Principale"):
            st.session_state.pagina = "chat"
            st.rerun()
            
        if st.button("📚 Catalogo Memorie"):
            st.session_state.pagina = "memoria"
            st.rerun()
            
        if st.session_state.ruolo == "admin":
            st.write("---")
            if st.button("🛡️ Pannello Admin"):
                st.session_state.pagina = "admin"
                st.rerun()
        
        st.write("---")
        if st.button("⚙️ Impostazioni"):
            st.session_state.pagina = "impostazioni"
            st.rerun()

        if st.button("🚪 Logout", type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. BARRA DI NAVIGAZIONE SUPERIORE (BACKUP SE LA TENDINA SPARISCE) ---
    col_tit, col_nav = st.columns([0.7, 0.3])
    with col_nav:
        if st.session_state.pagina != "chat":
            if st.button("⬅️ TORNA ALLA CHAT"):
                st.session_state.pagina = "chat"
                st.rerun()

    # --- 8. PAGINE ---

    # --- CHAT ---
    if st.session_state.pagina == "chat":
        st.markdown("<h3 style='text-align: center;'>Interfaccia Cognitiva</h3>", unsafe_allow_html=True)
        
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)

            if cervello:
                try:
                    res = cervello.elabora_concetto(st.session_state.utente, prompt)
                    with st.chat_message("assistant"): st.write(res)
                    st.session_state.history.append({"role": "assistant", "content": res})
                    
                    db = carica_db()
                    db[st.session_state.utente]["history"] = st.session_state.history
                    salva_db(db)
                except Exception as e: st.error(f"Errore IA: {e}")
            else: st.warning("IA non collegata.")

    # --- MEMORIA ---
    elif st.session_state.pagina == "memoria":
        st.title("📚 Catalogo Memorie")
        if cervello:
            mem = cervello.carica_memoria(st.session_state.utente)
            if mem:
                for k, v in mem.items():
                    st.markdown(f"<div class='mem-card'><strong>📌 {k}</strong><br>{v}</div>", unsafe_allow_html=True)
            else: st.info("Memoria vuota.")

    # --- ADMIN ---
    elif st.session_state.pagina == "admin" and st.session_state.ruolo == "admin":
        st.title("🛡️ Dashboard Admin")
        db = carica_db()
        for u_id, u_info in db.items():
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{u_id}**")
            c2.write(u_info['role'])
            if u_id != "admin" and c3.button("Elimina", key=f"del_{u_id}"):
                del db[u_id]
                salva_db(db)
                st.rerun()

    # --- IMPOSTAZIONI ---
    elif st.session_state.pagina == "impostazioni":
        st.title("⚙️ Impostazioni")
        if st.button("🗑️ Svuota Cronologia Chat"):
            st.session_state.history = []
            db = carica_db()
            db[st.session_state.utente]["history"] = []
            salva_db(db)
            st.success("Cronologia cancellata.")
