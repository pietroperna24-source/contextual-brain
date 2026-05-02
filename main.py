import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠", 
    layout="wide"
)

# --- 2. PULIZIA TOTALE INTERFACCIA ---
st.markdown("""
    <style>
        header {visibility: hidden; height: 0px;}
        footer {visibility: hidden; height: 0px;}
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        [data-testid="stHeader"] {background-color: rgba(0,0,0,0);}
        
        /* Rimuove ogni margine per occupare tutto il display */
        .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        
        * { -webkit-tap-highlight-color: transparent; }
    </style>
""", unsafe_allow_html=True)

        /* 3. Ottimizzazione spazi e bordi */
        .block-container {
            padding-top: 0rem; /* Portiamo tutto al limite superiore */
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        /* 4. Nasconde le icone di aiuto e i link sui titoli */
        .st-emotion-cache-10trblm {
            display: none;
        }
        
        /* 5. Impedisce l'evidenziazione blu al tocco (tipica del browser) */
        * {
            -webkit-tap-highlight-color: transparent;
            user-select: none; /* Rende l'app più simile a un'app reale */
        }
        
        /* Permette la selezione solo nei campi di testo */
        input, textarea {
            user-select: text;
        }

        /* Bottoni grandi per il touch dell'Honor */
        .stButton>button {
            border-radius: 15px;
            height: 3em;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGICA NOTIFICHE JS ---
def trigger_notifica(titolo, messaggio):
    js_code = f"""
    <script>
    function notify() {{
        if (Notification.permission === "granted") {{
            new Notification("{titolo}", {{ body: "{messaggio}" }});
        }} else {{
            Notification.requestPermission();
        }}
    }}
    notify();
    </script>
    """
    components.html(js_code, height=0)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
if 'utente_attuale' not in st.session_state:
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 5. FUNZIONI DATI ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = p
    with open("utenti.json", "w") as f: json.dump(db, f)

# --- 6. INTERFACCIA DI ACCESSO ---
if not st.session_state.autenticato:
    # Logo o Titolo centrato
    st.markdown("<h1 style='text-align: center; margin-top: 20px;'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
    
    t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
    
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        st.markdown("<br>", unsafe_allow_html=True) # Spazio extra
        if st.button("ACCEDI"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else:
                st.error("Credenziali errate")
    
    with t2:
        nuovo_u = st.text_input("Scegli Username", key="r_u")
        nuovo_p = st.text_input("Scegli Password", type="password", key="r_p")
        if st.button("CREA ACCOUNT"):
            if nuovo_u and nuovo_p:
                salva_utente(nuovo_u, nuovo_p)
                st.success("Account creato!")
            else:
                st.warning("Riempi tutti i campi!")

else:
    # --- 7. BARRA LATERALE ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Menù", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        st.divider()
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- 8. SEZIONI APP ---
    if scelta == "💬 Chat":
        st.title("💬 Chat")
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Di' qualcosa..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    if any(x in risposta.lower() for x in ["salvato", "memorizzato", "ricorderò"]):
                        trigger_notifica("Cervello Aggiornato", "Ho salvato tutto!")
                        st.toast("Ricordo salvato!", icon="🧠")
                except:
                    st.error("Errore connessione.")

    elif scelta == "🧠 Memoria":
        st.title("🧠 Memoria")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"):
                    st.write(v)
        else:
            st.info("Nessun ricordo.")

    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        if st.button("🔔 Attiva Notifiche"):
            components.html("<script>Notification.requestPermission();</script>", height=0)
            trigger_notifica("Sistema", "Notifiche attive!")
