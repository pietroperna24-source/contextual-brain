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

# --- 2. FUNZIONE NOTIFICHE (JavaScript) ---
def trigger_notifica(titolo, messaggio):
    # Questo codice JS chiede il permesso e invia la notifica di sistema
    js_code = f"""
    <script>
    function notifyMe() {{
      if (!("Notification" in window)) {{
        console.log("Browser non supporta notifiche");
      }} else if (Notification.permission === "granted") {{
        new Notification("{titolo}", {{ body: "{messaggio}", icon: "https://cdn-icons-png.flaticon.com/512/4712/4712139.png" }});
      }} else if (Notification.permission !== "denied") {{
        Notification.requestPermission().then(function (permission) {{
          if (permission === "granted") {{
            new Notification("{titolo}", {{ body: "{messaggio}" }});
          }}
        }});
      }}
    }}
    notifyMe();
    </script>
    """
    components.html(js_code, height=0)

# --- 3. CSS CUSTOM ---
st.markdown("""
    <style>
    .stChatInputContainer { padding-bottom: 20px; }
    .stChatMessage { border-radius: 15px; }
    [data-testid="stSidebar"] { background-color: #111111; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- 5. LOGICA ACCESSO ---
if not st.session_state.autenticato:
    st.title("🧠 Accesso al Cervello")
    tab_l, tab_r = st.tabs(["Accedi", "Registrati"])
    
    with tab_l:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("LOG IN"):
            if os.path.exists("utenti.json"):
                with open("utenti.json", "r") as f: db = json.load(f)
                if u in db and db[u] == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.rerun()
                else: st.error("Errore credenziali")

    with tab_r:
        nuovo_u = st.text_input("Nuovo User")
        nuovo_p = st.text_input("Nuova Pass", type="password")
        if st.button("CREA"):
            db = {}
            if os.path.exists("utenti.json"):
                with open("utenti.json", "r") as f: db = json.load(f)
            db[nuovo_u] = nuovo_p
            with open("utenti.json", "w") as f: json.dump(db, f)
            st.success("Fatto! Accedi ora.")

else:
    # --- 6. APP PRINCIPALE ---
    with st.sidebar:
        st.title(f"Ciao {st.session_state.utente_attuale}")
        scelta = st.radio("Menu", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        if st.button("Logout"):
            st.session_state.autenticato = False
            st.rerun()

    if scelta == "💬 Chat":
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            with st.chat_message("assistant"):
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.markdown(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                # SE L'IA HA SALVATO QUALCOSA, MANDIAMO LA NOTIFICA
                if "Ho memorizzato" in risposta:
                    trigger_notifica("Promemoria Salvato!", risposta)
                    st.toast("Notifica inviata!", icon="🔔")

    elif scelta == "🧠 Memoria":
        st.title("Cosa ricordo")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        st.json(mem)

    elif scelta == "⚙️ Impostazioni":
        st.button("🔔 Attiva Notifiche", on_click=lambda: trigger_notifica("Test", "Notifiche attivate!"))
