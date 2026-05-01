import streamlit as st
import cervello
import json
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual", 
    page_icon="🧠",
    layout="centered"
)

# --- 2. LOGO E STILE CSS PER MOBILE ---
def applica_estetica():
    # URL di un logo moderno (puoi cambiarlo con il tuo)
    url_logo = "https://cdn-icons-png.flaticon.com/512/4712/4712139.png"
    
    st.markdown(f"""
        <style>
            /* Centra il logo */
            .logo-container {{
                display: flex;
                justify-content: center;
                margin-bottom: 20px;
            }}
            .logo-img {{
                width: 100px;
            }}
            /* Rende i bottoni grandi per il touch del cellulare */
            div.stButton > button:first-child {{
                height: 3.5em;
                width: 100%;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
                background-color: #00ffcc;
                color: #1e1e1e;
                border: none;
            }}
            /* Stile per i box di input */
            .stTextInput > div > div > input {{
                border-radius: 10px;
            }}
        </style>
        <div class="logo-container">
            <img class="logo-img" src="{url_logo}">
        </div>
        """, unsafe_allow_html=True)

# --- 3. FUNZIONI GESTIONE UTENTI ---
UTENTI_FILE = "utenti.json"

def carica_utenti():
    if not os.path.exists(UTENTI_FILE):
        return {}
    with open(UTENTI_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def salva_nuovo_utente(username, password):
    utenti = carica_utenti()
    utenti[username] = password
    with open(UTENTI_FILE, "w") as f:
        json.dump(utenti, f)

# --- 4. LOGICA DI ACCESSO ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None

applica_estetica()

if not st.session_state.autenticato:
    st.title("Benvenuto nel tuo Cervello")
    tab1, tab2 = st.tabs(["🔑 Accedi", "📝 Registrati"])
    
    with tab1:
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pwd")
        if st.button("ACCEDI"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else:
                st.error("Credenziali non corrette.")

    with tab2:
        nuovo_u = st.text_input("Scegli un Username", key="reg_user")
        nuovo_p = st.text_input("Scegli una Password", type="password", key="reg_pwd")
        if st.button("CREA ACCOUNT"):
            db = carica_utenti()
            if nuovo_u in db:
                st.warning("Questo username esiste già.")
            elif nuovo_u == "" or nuovo_p == "":
                st.error("Compila tutti i campi.")
            else:
                salva_nuovo_utente(nuovo_u, nuovo_p)
                st.success("Registrazione completata! Ora puoi accedere.")

else:
    # --- 5. INTERFACCIA APP PRINCIPALE (DOPO IL LOGIN) ---
    st.sidebar.title(f"Ciao, {st.session_state.utente_attuale}")
    if st.sidebar.button("Esci"):
        st.session_state.autenticato = False
        st.session_state.utente_attuale = None
        st.rerun()

    st.title("🧠 Memoria Attiva")
    
    input_utente = st.text_area("Cosa vuoi che io ricordi o chiedermi?", placeholder="Esempio: Ricorda che il mio codice cliente è A10")
    
    if st.button("🚀 ELABORA"):
        if input_utente:
            with st.spinner("L'IA sta pensando..."):
                # Salviamo l'input nel file temporaneo per il modulo cervello
                with open("input_recente.txt", "w", encoding="utf-8") as f:
                    f.write(input_utente)
                
                # Passiamo l'utente attuale alla funzione del cervello
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, input_utente)
                
                st.chat_message("assistant").write(risposta)
        else:
            st.warning("Scrivi qualcosa prima di inviare.")

    # Expander per visualizzare i dati salvati
    with st.sidebar.expander("📂 La tua Memoria"):
        memoria_user = f"memoria_{st.session_state.utente_attuale}.json"
        if os.path.exists(memoria_user):
            with open(memoria_user, "r", encoding="utf-8") as f:
                st.json(json.load(f))
        else:
            st.write("Ancora nulla in memoria.")
