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
    page_title="Cervello Contextual Ultimate",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UI ENGINE (JS & CSS) ---
# Pulizia elementi Streamlit e gestione scroll
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
        .stApp { background-color: #F8F9FB; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #EAEAEA; }
        
        /* Toolbar Superiore Fissa */
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            background: white;
            border-radius: 10px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        /* Bottoni */
        .stButton>button {
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        /* Box Memoria nel Catalogo */
        .mem-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #6C5CE7;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. GESTIONE DATI (DATABASE) ---
DB_FILE = "utenti.json"

def inizializza_db():
    if not os.path.exists(DB_FILE):
        default_db = {
            "admin": {
                "pass": "admin123", 
                "history": [], 
                "role": "admin",
                "settings": {"theme": "light"}
            }
        }
        salva_db(default_db)

def carica_db():
    inizializza_db()
    with open(DB_FILE, "r") as f:
        return json.load(f)

def salva_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente': None,
        'ruolo': 'user',
        'history': [],
        'pagina': 'chat'
    })

# --- 5. LOGICA DI ACCESSO ---
if not st.session_state.autenticato:
    _, col_c, _ = st.columns([1, 1.5, 1])
    with col_c:
        st.write("##")
        st.markdown("<h1 style='text-align: center;'>🧠 Cervello Contextual</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 Entra", "📝 Registrati"])
        
        with tab_log:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDI", use_container_width=True):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True,
                        'utente': u,
                        'ruolo': db[u].get("role", "user"),
                        'history': db[u].get("history", [])
                    })
                    st.rerun()
                else:
                    st.error("Credenziali errate.")

        with tab_reg:
            nu = st.text_input("Scegli Username")
            np = st.text_input("Scegli Password", type="password")
            if st.button("CREA ACCOUNT", use_container_width=True):
                db = carica_db()
                if nu and nu not in db:
                    db[nu] = {"pass": np, "history": [], "role": "user"}
                    salva_db(db)
                    st.success("Registrazione completata!")
                else:
                    st.warning("Username non disponibile.")

else:
    # --- 6. SIDEBAR & MENU ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente.upper()}")
        st.caption(f"Livello Accesso: {st.session_state.ruolo}")
        st.write("---")
        
        if st.button("💬 Chat AI", use_container_width=True):
            st.session_state.pagina = "chat"
            st.rerun()
            
        if st.button("📚 Catalogo Memorie", use_container_width=True):
            st.session_state.pagina = "memoria"
            st.rerun()
            
        if st.session_state.ruolo == "admin":
            st.write("---")
            if st.button("🛡️ Dashboard Admin", use_container_width=True):
                st.session_state.pagina = "admin"
                st.rerun()
        
        st.write("---")
        if st.button("⚙️ Impostazioni", use_container_width=True):
            st.session_state.pagina = "impostazioni"
            st.rerun()

        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. NAVIGAZIONE (Tasto Indietro) ---
    if st.session_state.pagina != "chat":
        col_tit, col_back = st.columns([0.8, 0.2])
        with col_back:
            if st.button("⬅️ INDIETRO", use_container_width=True):
                st.session_state.pagina = "chat"
                st.rerun()

    # --- 8. LOGICA DELLE PAGINE ---

    # --- PAGINA: CHAT ---
    if st.session_state.pagina == "chat":
        st.markdown(f"<h3 style='text-align: center;'>Conversazione con il Brain</h3>", unsafe_allow_html=True)
        
        # Visualizzazione cronologia
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Input Chat
        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            # Elaborazione tramite modulo cervello
            if cervello:
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente, prompt)
                    with st.chat_message("assistant"):
                        st.write(risposta)
                    st.session_state.history.append({"role": "assistant", "content": risposta})
                    
                    # Salvataggio nel DB
                    db = carica_db()
                    db[st.session_state.utente]["history"] = st.session_state.history
                    salva_db(db)
                except Exception as e:
                    st.error(f"Errore tecnico: {e}")
            else:
                st.warning("IA non collegata.")

    # --- PAGINA: MEMORIA (CATALOGO) ---
    elif st.session_state.pagina == "memoria":
        st.title("📚 Catalogo Memorie")
        st.write("Ecco i concetti salvati nel tuo cervello contestuale:")
        
        if cervello:
            try:
                mem = cervello.carica_memoria(st.session_state.utente)
                if mem:
                    for chiave, valore in mem.items():
                        st.markdown(f"""
                        <div class="mem-card">
                            <strong>📌 {chiave}</strong><br>
                            <small>{valore}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("La memoria è ancora vuota.")
            except:
                st.error("Impossibile leggere la memoria.")

    # --- PAGINA: ADMIN ---
    elif st.session_state.pagina == "admin" and st.session_state.ruolo == "admin":
        st.title("🛡️ Amministrazione Sistema")
        db = carica_db()
        
        tab_utenti, tab_sistema = st.tabs(["Utenti", "Stato Sistema"])
        
        with tab_utenti:
            for user, data in db.items():
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{user}**")
                c2.write(f"Ruolo: {data['role']}")
                if user != "admin":
                    if c3.button("Elimina", key=f"del_{user}"):
                        del db[user]
                        salva_db(db)
                        st.rerun()
        
        with tab_sistema:
            st.metric("Utenti Totali", len(db))
            st.write("Il database è localizzato in:", os.path.abspath(DB_FILE))

    # --- PAGINA: IMPOSTAZIONI ---
    elif st.session_state.pagina == "impostazioni":
        st.title("⚙️ Impostazioni Profilo")
        if st.button("🗑️ Svuota Cronologia Chat"):
            st.session_state.history = []
            db = carica_db()
            db[st.session_state.utente]["history"] = []
            salva_db(db)
            st.success("Cronologia svuotata correttamente.")
