import streamlit as st
import cervello
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cervello Contextual", page_icon="🧠", layout="wide")

# --- 2. LOGICA NOTIFICHE JS ---
def trigger_notifica(titolo, messaggio):
    js_code = f"""
    <script>
    if (Notification.permission === "granted") {{
        new Notification("{titolo}", {{ body: "{messaggio}", icon: "https://cdn-icons-png.flaticon.com/512/4712/4712139.png" }});
    }} else if (Notification.permission !== "denied") {{
        Notification.requestPermission();
    }}
    </script>
    """
    components.html(js_code, height=0)

# --- 3. INIZIALIZZAZIONE SESSION STATE ---
# (Aggiunto controllo più solido per evitare errori di variabili mancanti)
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
if 'utente_attuale' not in st.session_state:
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 4. FUNZIONI DATI (Mancava il controllo errori qui) ---
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

# --- 5. INTERFACCIA ---
if not st.session_state.autenticato:
    st.title("🧠 Accesso Protetto")
    t1, t2 = st.tabs(["Login", "Registrazione"])
    
    with t1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("LOG IN"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else:
                st.error("Credenziali errate")
    
    with t2:
        nuovo_u = st.text_input("Nuovo User", key="reg_u")
        nuovo_p = st.text_input("Nuova Pass", type="password", key="reg_p")
        if st.button("CREA ACCOUNT"):
            if nuovo_u and nuovo_p:
                salva_utente(nuovo_u, nuovo_p)
                st.success("Fatto! Ora puoi accedere.")
            else:
                st.warning("Compila tutto!")

else:
    # --- APP DOPO IL LOGIN ---
    with st.sidebar:
        st.header(f"👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Navigazione", ["💬 Chat", "🧠 Memoria", "⚙️ Settings"])
        if st.button("Esci"):
            st.session_state.autenticato = False
            st.session_state.chat_history = [] # Pulizia automatica
            st.rerun()

    if scelta == "💬 Chat":
        st.title("💬 Chat")
        
        # Mostra cronologia
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # Input Chat
        if prompt := st.chat_input("Scrivi al tuo cervello..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                # Passiamo l'utente al cervello per la memoria specifica
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.markdown(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                # TRIGGER NOTIFICA se l'IA ha memorizzato
                if "Ho memorizzato" in risposta:
                    trigger_notifica("Cervello Aggiornato", "Ho salvato un nuovo dato!")
                    st.toast("✅ Notifica inviata", icon="🔔")

    elif scelta == "🧠 Memoria":
        st.title("🧠 Database Personale")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                st.info(f"**{k}**: {v}")
        else:
            st.write("Nulla in memoria.")

    elif scelta == "⚙️ Settings":
        st.title("⚙️ Impostazioni")
        if st.button("🔔 Prova Notifica"):
            trigger_notifica("Test", "Funzionano!")
