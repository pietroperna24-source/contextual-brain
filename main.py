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

# --- 2. DESIGN & PULIZIA INTERFACCIA ---
st.markdown("""
    <style>
        /* Nasconde header, footer e badge Streamlit */
        header, footer, #MainMenu, .stDeployButton, .viewerBadge_container__1QSob {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Forza il layout a tutto schermo */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }

        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }

        /* Styling Titoli */
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
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }

        /* Bottoni */
        div.stButton > button {
            border-radius: 12px;
            background-color: #6C5CE7;
            color: white;
            font-weight: 600;
            height: 3rem;
            border: none;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            background-color: #5849C4;
            transform: translateY(-1px);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNZIONI DATI (Persistenza Cronologia) ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = {"password": p, "history": []}
    with open("utenti.json", "w") as f: json.dump(db, f)

def salva_cronologia(u, history):
    db = carica_utenti()
    if u in db:
        db[u]["history"] = history
        with open("utenti.json", "w") as f: json.dump(db, f)

# --- 4. LOGICA NOTIFICHE ---
def trigger_notifica(titolo, messaggio):
    js = f"<script>new Notification('{titolo}', {{body: '{messaggio}'}});</script>"
    components.html(js, height=0)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
if 'utente_attuale' not in st.session_state:
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 6. INTERFACCIA ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.1, 0.8, 0.1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Accedi alla tua memoria aumentata</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("ACCEDI", use_container_width=True):
                db = carica_utenti()
                # Verifica se l'utente esiste e la password coincide
                if u in db and (isinstance(db[u], dict) and db[u].get("password") == p):
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    # Caricamento cronologia salvata
                    st.session_state.chat_history = db[u].get("history", [])
                    st.rerun()
                elif u in db and db[u] == p: # Gestione per vecchi account (solo stringa)
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        
        with t2:
            nuovo_u = st.text_input("Scegli Username", key="reg_u")
            nuovo_p = st.text_input("Scegli Password", type="password", key="reg_p")
            if st.button("CREA ACCOUNT", use_container_width=True):
                if nuovo_u and nuovo_p:
                    salva_utente(nuovo_u, nuovo_p)
                    st.success("Account creato! Ora effettua il login.")
                else:
                    st.warning("Inserisci tutti i dati.")

else:
    # --- 7. BARRA LATERALE ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Navigazione", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        if st.button("Esci"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. CHAT ---
    if scelta == "💬 Chat":
        st.write(f"### Chat con il Cervello")
        
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            # Aggiunta messaggio utente
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.write(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    # Salvataggio automatico su file
                    salva_cronologia(st.session_state.utente_attuale, st.session_state.chat_history)
                    
                    if any(x in risposta.lower() for x in ["salvato", "ricorderò"]):
                        st.toast("Ricordo archiviato!", icon="🧠")
                except Exception as e:
                    st.error(f"Errore: {e}")

    # --- 9. MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Memoria Esterna")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"):
                        st.write(v)
            else:
                st.info("Nessun dato salvato.")
        except:
            st.error("Impossibile leggere la memoria.")

    # --- 10. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        if st.button("🗑️ Cancella Cronologia Chat"):
            st.session_state.chat_history = []
            salva_cronologia(st.session_state.utente_attuale, [])
            st.rerun()
