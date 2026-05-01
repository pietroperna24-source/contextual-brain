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

# --- 2. LOGICA NOTIFICHE JS (Il "Ponte" Browser) ---
def trigger_notifica(titolo, messaggio):
    # Questo codice chiede il permesso se non c'è, e invia la notifica
    js_code = f"""
    <script>
    function notify() {{
        if (Notification.permission === "granted") {{
            new Notification("{titolo}", {{ 
                body: "{messaggio}", 
                icon: "https://cdn-icons-png.flaticon.com/512/4712/4712139.png" 
            }});
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission();
        }}
    }}
    notify();
    </script>
    """
    components.html(js_code, height=0)

# --- 3. SESSION STATE (Gestione variabili) ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
if 'utente_attuale' not in st.session_state:
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 4. FUNZIONI DATI UTENTI ---
def carica_utenti():
    if not os.path.exists("utenti.json"):
        return {}
    try:
        with open("utenti.json", "r") as f:
            return json.load(f)
    except:
        return {}

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = p
    with open("utenti.json", "w") as f:
        json.dump(db, f)

# --- 5. INTERFACCIA DI ACCESSO ---
if not st.session_state.autenticato:
    st.markdown("<h1 style='text-align: center;'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
    
    with t1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
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
                st.success("Account creato con successo! Ora fai il login.")
            else:
                st.warning("Riempi tutti i campi!")

else:
    # --- 6. BARRA LATERALE ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Navigazione", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        st.divider()
        if st.button("Esci dall'account"):
            st.session_state.autenticato = False
            st.session_state.utente_attuale = None
            st.session_state.chat_history = []
            st.rerun()

    # --- 7. SEZIONI APP ---
    if scelta == "💬 Chat":
        st.title("💬 Assistente Intelligente")
        
        # Mostra i messaggi precedenti
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # Input della chat
        if prompt := st.chat_input("Di' qualcosa..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.markdown(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                # SE L'IA HA SALVATO, INVIO NOTIFICA
                if "Ho memorizzato" in risposta or "Ho salvato" in risposta:
                    trigger_notifica("Cervello Aggiornato", "Nuovo promemoria salvato con successo!")
                    st.toast("Notifica inviata!", icon="🔔")

    elif scelta == "🧠 Memoria":
        st.title("🧠 La tua Memoria")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"):
                    st.write(v)
        else:
            st.info("Non ho ancora ricordi per te. Prova a dirmi: 'Ricorda che...'")

    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        st.subheader("Notifiche")
        if st.button("🔔 Attiva/Testa Notifiche"):
            # Forza la richiesta di permesso al browser
            components.html("<script>Notification.requestPermission();</script>", height=0)
            trigger_notifica("Test", "Se vedi questo, le notifiche sono attive!")
