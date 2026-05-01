import streamlit as st
import cervello
import json
import os

def invia_notifica_browser(titolo, messaggio):
    js_notifica = f"""
    <script>
    if (Notification.permission === "granted") {{
        new Notification("{titolo}", {{ body: "{messaggio}" }});
    }} else if (Notification.permission !== "denied") {{
        Notification.requestPermission().then(permission => {{
            if (permission === "granted") {{
                new Notification("{titolo}", {{ body: "{messaggio}" }});
            }}
        }});
    }}
    </script>
    """
    st.components.v1.html(js_notifica, height=0)
    
# --- 1. CONFIGURAZIONE PAGINA (Indispensabile per l'icona e il titolo dell'app) ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM (Ottimizzazione per schermi touch e Mobile) ---
st.markdown("""
    <style>
    /* Nasconde i menu standard di Streamlit per un look più pulito */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Personalizzazione Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333;
    }
    
    /* Bottoni della Sidebar */
    .stRadio > div { gap: 15px; }
    .stRadio label { 
        background-color: #1e1e1e; 
        padding: 12px 20px; 
        border-radius: 12px; 
        cursor: pointer;
        transition: 0.3s;
    }
    .stRadio label:hover { border: 1px solid #00ffcc; }

    /* Stile bolle Chat */
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    
    /* Logo circolare */
    .logo-container { text-align: center; padding: 10px; }
    .logo-img { border-radius: 50%; border: 2px solid #00ffcc; box-shadow: 0 0 15px #00ffcc44; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INIZIALIZZAZIONE SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 4. FUNZIONI DI GESTIONE DATI ---
UTENTI_FILE = "utenti.json"

def carica_utenti():
    if not os.path.exists(UTENTI_FILE): return {}
    with open(UTENTI_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def salva_nuovo_utente(user, pwd):
    utenti = carica_utenti()
    utenti[user] = pwd
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f)

# --- 5. LOGICA DI ACCESSO (LOGIN / REGISTRAZIONE) ---
if not st.session_state.autenticato:
    st.markdown('<div class="logo-container"><img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="100" class="logo-img"></div>', unsafe_allow_html=True)
    st.title("🧠 Benvenuto nel tuo Cervello")
    
    tab_log, tab_reg = st.tabs(["🔑 Accedi", "📝 Crea Account"])
    
    with tab_log:
        u = st.text_input("Username", key="l_user")
        p = st.text_input("Password", type="password", key="l_pwd")
        if st.button("LOG IN", type="primary"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else:
                st.error("Credenziali non corrette")

    with tab_reg:
        nuovo_u = st.text_input("Scegli un Username", key="r_user")
        nuovo_p = st.text_input("Scegli una Password", type="password", key="r_pwd")
        if st.button("REGISTRATI"):
            db = carica_utenti()
            if nuovo_u in db:
                st.warning("Username già occupato")
            elif nuovo_u and nuovo_p:
                salva_nuovo_utente(nuovo_u, nuovo_p)
                st.success("Account creato! Ora fai il login")
            else:
                st.error("Riempi tutti i campi")

else:
    # --- 6. INTERFACCIA PRINCIPALE (SIDEBAR) ---
    with st.sidebar:
        st.markdown(f'<div class="logo-container"><img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="60" class="logo-img"></div>', unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center;'>Ciao, {st.session_state.utente_attuale}</h3>", unsafe_allow_html=True)
        st.write("---")
        
        scelta = st.radio("Scegli sezione:", ["💬 Assistente", "🧠 Memoria", "⚙️ Impostazioni"])
        
        st.write("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.autenticato = False
            st.session_state.utente_attuale = None
            st.session_state.chat_history = []
            st.rerun()

    # --- 7. NAVIGAZIONE FRA LE SEZIONI ---
    
    # SEZIONE CHAT
    if scelta == "💬 Assistente":
        st.title("💬 Chat Intelligente")
        
        # Mostra la cronologia
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input utente
        if prompt := st.chat_input("Chiedimi qualsiasi cosa..."):
            # Aggiungi messaggio utente alla storia
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Genera risposta IA
            with st.chat_message("assistant"):
                with st.spinner("Sto consultando la tua memoria..."):
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})

    # SEZIONE MEMORIA
    elif scelta == "🧠 Memoria":
        st.title("🧠 Archivio Memoria")
        st.write("Qui ci sono tutte le informazioni che ho salvato per te.")
        
        dati = cervello.carica_memoria(st.session_state.utente_attuale)
        if dati:
            for chiave, valore in dati.items():
                with st.expander(f"📍 {chiave.upper()}"):
                    st.write(valore)
        else:
            st.info("La tua memoria è ancora vuota. Prova a dirmi: 'Ricorda che...'")

    # SEZIONE IMPOSTAZIONI
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Personalizzazione")
        st.write(f"Account attivo: **{st.session_state.utente_attuale}**")
        
        st.divider()
        st.subheader("Gestione Dati")
        if st.button("🧹 Svuota cronologia chat"):
            st.session_state.chat_history = []
            st.success("Cronologia pulita!")
            st.rerun()
            
        if st.button("⚠️ Elimina tutta la memoria (Reset)"):
            file_m = f"memoria_{st.session_state.utente_attuale}.json"
            if os.path.exists(file_m):
                os.remove(file_m)
                st.success("Memoria formattata con successo.")
            else:
                st.info("Nessun database di memoria trovato.")
