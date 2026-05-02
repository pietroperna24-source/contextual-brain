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

# --- 2. DESIGN & STYLING CUSTOM (ARMORMONIA HOME) ---
st.markdown("""
    <style>
        /* Nascondi elementi standard */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container { padding-top: 2rem; }

        /* Sfondo gradiente leggero */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }

        /* Styling Titoli e Testi */
        .main-title {
            font-size: 3rem;
            font-weight: 800;
            color: #2D3436;
            text-align: center;
            margin-bottom: 0.2rem;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .sub-title {
            text-align: center;
            color: #636E72;
            margin-bottom: 2rem;
        }

        /* Bottoni personalizzati */
        div.stButton > button {
            border-radius: 12px;
            background-color: #6C5CE7;
            color: white;
            border: none;
            padding: 0.6rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #5849C4;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
        }

        /* Input Fields */
        .stTextInput input {
            border-radius: 10px;
        }
        
        /* Tabs Centralizzate */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            justify-content: center;
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

# --- 6. INTERFACCIA ACCESSO (HOME) ---
if not st.session_state.autenticato:
    st.write("##") # Spacer
    col_l, col_c, col_r = st.columns([1, 2, 1])
    
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Accedi alla tua estensione cognitiva digitale</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            st.write("##")
            u = st.text_input("Username", key="l_user", placeholder="Il tuo nome")
            p = st.text_input("Password", type="password", key="l_pass", placeholder="••••••••")
            st.write("##")
            if st.button("ACCEDI AL CERVELLO", use_container_width=True):
                db = carica_utenti()
                if u in db and db[u] == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.toast(f"Connessione stabilita. Bentornato {u}!", icon="🧠")
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")
        
        with t2:
            st.write("##")
            nuovo_u = st.text_input("Nuovo Username", key="r_user")
            nuovo_p = st.text_input("Nuova Password", type="password", key="r_pass")
            st.write("##")
            if st.button("CREA ACCOUNT", use_container_width=True):
                if nuovo_u and nuovo_p:
                    salva_utente(nuovo_u, nuovo_p)
                    st.success("Account creato! Ora effettua il login.")
                else:
                    st.warning("Compila tutti i campi!")

else:
    # --- 7. BARRA LATERALE ---
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center;'>👤 {st.session_state.utente_attuale}</h2>", unsafe_allow_html=True)
        st.divider()
        scelta = st.radio("NAVIGAZIONE", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        st.divider()
        if st.button("Esci dal Sistema", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- 8. SEZIONE CHAT ---
    if scelta == "💬 Chat":
        st.markdown(f"### Chat con il tuo Cervello")
        
        # Display messaggi
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Di cosa vuoi parlare?"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    # Logica notifica intelligente
                    if any(x in risposta.lower() for x in ["memorizzato", "salvato", "ricorderò", "appreso"]):
                        trigger_notifica("Memoria Aggiornata", "Ho acquisito una nuova informazione.")
                        st.toast("Nuovo ricordo salvato!", icon="✨")
                except Exception as e:
                    st.error(f"Errore di elaborazione: {e}")

    # --- 9. SEZIONE MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Archivio Cognitivo")
        st.info("Qui trovi tutto ciò che ho imparato su di te e sulle tue preferenze.")
        
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"):
                        st.write(v)
                        if st.button(f"Dimentica {k}", key=f"del_{k}"):
                            st.warning("Funzionalità di eliminazione in fase di test.")
            else:
                st.write("Nessun dato memorizzato al momento.")
        except:
            st.error("Errore nel caricamento dei dati di memoria.")

    # --- 10. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Configurazione")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Notifiche")
            if st.button("🔔 Testa Notifiche Browser"):
                components.html("<script>Notification.requestPermission();</script>", height=0)
                trigger_notifica("Test Sistema", "Le notifiche sono attive!")
        with col2:
            st.subheader("Dati")
            if st.button("🗑️ Svuota Cronologia Chat"):
                st.session_state.chat_history = []
                st.rerun()
