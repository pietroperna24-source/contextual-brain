import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. JS AGGRESSIVO (Rimuove badge, corone e barre di sistema) ---
# Questo script agisce sulla pagina "padre" per eliminare i widget di Codespaces
components.html("""
    <script>
    const hideExtraElements = () => {
        const selectors = [
            ".viewerBadge_container__1QSob", 
            ".stDeployButton", 
            "footer", 
            "#MainMenu",
            "header"
        ];
        selectors.forEach(s => {
            const el = window.parent.document.querySelector(s);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(hideExtraElements, 500);
    </script>
""", height=0)

# --- 3. CSS PER ARMONIA E DESIGN MOBILE ---
st.markdown("""
    <style>
        /* Pulizia totale */
        header, footer, .stDeployButton { visibility: hidden !important; height: 0; }
        
        /* Sfondo e Layout */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }

        /* Titoli stilizzati */
        .main-title {
            font-size: 2.5rem;
            font-weight: 800;
            text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .sub-title {
            text-align: center;
            color: #636E72;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }

        /* Pulsanti arrotondati */
        div.stButton > button {
            border-radius: 12px;
            background-color: #6C5CE7;
            color: white;
            font-weight: 600;
            border: none;
            height: 3rem;
            transition: 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #5849C4;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(108, 92, 231, 0.2);
        }

        /* Tabs centralizzate */
        .stTabs [data-baseweb="tab-list"] {
            gap: 15px;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. GESTIONE DATI (Database JSON) ---
def carica_db():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f: json.dump(db, f, indent=4)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'chat_history': []
    })

# --- 6. INTERFACCIA DI ACCESSO (HOME) ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.05, 0.9, 0.05])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>La tua memoria aumentata, sempre con te</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="l_user")
            p = st.text_input("Password", type="password", key="l_pass")
            if st.button("ACCEDI", use_container_width=True):
                db = carica_db()
                if u in db and db[u].get("pass") == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.session_state.chat_history = db[u].get("history", [])
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        
        with t2:
            nuovo_u = st.text_input("Scegli Username", key="r_user")
            nuovo_p = st.text_input("Scegli Password", type="password", key="r_pass")
            if st.button("CREA ACCOUNT", use_container_width=True):
                if nuovo_u and nuovo_p:
                    db = carica_db()
                    db[nuovo_u] = {"pass": nuovo_p, "history": []}
                    salva_db(db)
                    st.success("Account creato! Ora effettua il login.")
                else:
                    st.warning("Inserisci tutti i dati richiesti.")

else:
    # --- 7. BARRA LATERALE ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale}")
        scelta = st.radio("VAI A:", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        st.divider()
        if st.button("Esci dal Sistema", use_container_width=True):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. SEZIONE CHAT (Con salvataggio automatico) ---
    if scelta == "💬 Chat":
        st.markdown("### 💬 Conversazione")
        
        # Mostra cronologia
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Di cosa vuoi parlare?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    # Persistenza: salva nel file JSON
                    db = carica_db()
                    if st.session_state.utente_attuale in db:
                        db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                        salva_db(db)
                    
                    if any(x in risposta.lower() for x in ["salvato", "memorizzato"]):
                        st.toast("Ricordo salvato!", icon="🧠")
                except Exception as e:
                    st.error(f"Errore di connessione: {e}")

    # --- 9. SEZIONE MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Archivio Memoria")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"):
                        st.write(v)
            else:
                st.info("La tua memoria è ancora vuota. Inizia a chattare per popolarla!")
        except:
            st.error("Errore nel caricamento della memoria.")

    # --- 10. SEZIONE IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Gestione Dati")
        if st.button("🗑️ Svuota Cronologia Chat", use_container_width=True):
            st.session_state.chat_history = []
            db = carica_db()
            if st.session_state.utente_attuale in db:
                db[st.session_state.utente_attuale]["history"] = []
                salva_db(db)
            st.success("Cronologia eliminata!")
            st.rerun()
