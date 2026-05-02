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

# --- 2. RIMOZIONE BARRA GITHUB E MENU ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        .stButton>button {
            border-radius: 20px;
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

# --- 5. FUNZIONI DATI (AGGIUNTA: Salvataggio Cronologia) ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    with open("utenti.json", "r") as f: return json.load(f)

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = p
    with open("utenti.json", "w") as f: json.dump(db, f)

# --- 6. INTERFACCIA ACCESSO ---
if not st.session_state.autenticato:
    st.markdown("<h1 style='text-align: center;'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
    
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ACCEDI", use_container_width=True):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                # Carichiamo la cronologia salvata se esiste (Mancava!)
                st.rerun()
            else:
                st.error("Credenziali errate")
    
    with t2:
        nuovo_u = st.text_input("Scegli Username")
        nuovo_p = st.text_input("Scegli Password", type="password")
        if st.button("CREA ACCOUNT", use_container_width=True):
            if nuovo_u and nuovo_p:
                salva_utente(nuovo_u, nuovo_p)
                st.success("Account creato!")
            else:
                st.warning("Campi vuoti!")

else:
    # --- 7. BARRA LATERALE ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Vai a:", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        if st.button("Esci", use_container_width=True):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

    # --- 8. SEZIONE CHAT (Ottimizzata) ---
    if scelta == "💬 Chat":
        st.title("💬 Chat")
        
        # Container per i messaggi (per evitare scroll infiniti)
        chat_container = st.container()
        
        with chat_container:
            for msg in st.session_state.chat_history:
                st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                try:
                    # Chiamata al modulo cervello con gestione errore
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    if any(x in risposta for x in ["memorizzato", "salvato", "ricorderò"]):
                        trigger_notifica("Cervello Aggiornato", "Ho salvato l'informazione!")
                        st.toast("Ricordo salvato!", icon="🧠")
                except Exception as e:
                    st.error(f"Errore di connessione al cervello: {e}")

    # --- 9. SEZIONE MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Memoria")
        try:
            mem = cervello.carica_memoria(st.session_state.utente_attuale)
            if mem:
                for k, v in mem.items():
                    with st.expander(f"📌 {k}"):
                        st.write(v)
                        if st.button(f"Elimina {k}", key=k):
                            # Qui andrebbe una funzione cervello.elimina_ricordo
                            st.warning("Funzione elimina non ancora implementata")
            else:
                st.info("La tua memoria è vuota.")
        except:
            st.error("Impossibile caricare la memoria.")

    # --- 10. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        if st.button("🔔 Attiva Notifiche"):
            components.html("<script>Notification.requestPermission();</script>", height=0)
            trigger_notifica("Test", "Funzionano!")
