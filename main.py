import streamlit as st
import cervello
import json
import os

# --- 1. CONFIGURAZIONE PAGINA (Deve essere la prima istruzione) ---
st.set_page_config(page_title="Cervello Contextual v2", page_icon="🧠", layout="wide")

# --- 2. CSS AVANZATO (Mancava per rendere tutto fluido su mobile) ---
st.markdown("""
    <style>
    /* Sfondo e font */
    .main { background-color: #0e1117; color: white; }
    
    /* Input della chat in basso */
    .stChatInputContainer { padding-bottom: 20px; }
    
    /* Bottoni della sidebar più grandi per il pollice */
    .stRadio > div { gap: 10px; }
    .stRadio label { 
        background-color: #262730; 
        padding: 10px 20px; 
        border-radius: 10px; 
        width: 100%;
        display: block;
    }
    
    /* Logo circolare */
    .logo-img {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius: 50%;
        border: 2px solid #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. GESTIONE STATO DELLA SESSIONE ---
if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [] # Per non perdere i messaggi quando cambi tab

# --- 4. FUNZIONI DI SERVIZIO ---
def carica_utenti():
    if not os.path.exists("utenti.json"): return {}
    with open("utenti.json", "r") as f: 
        try: return json.load(f)
        except: return {}

def salva_utente(u, p):
    db = carica_utenti()
    db[u] = p
    with open("utenti.json", "w") as f: json.dump(db, f)

# --- 5. LOGICA DI ACCESSO ---
if not st.session_state.autenticato:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div style="text-align:center"><img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="100" class="logo-img"></div>', unsafe_allow_html=True)
        st.title("Accedi al Cervello")
        
        tab_login, tab_reg = st.tabs(["Login", "Nuovo Account"])
        
        with tab_login:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("LOG IN"):
                db = carica_utenti()
                if u in db and db[u] == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.rerun()
                else: st.error("Credenziali errate")
        
        with tab_reg:
            nuovo_u = st.text_input("Scegli Username", key="r_u")
            nuovo_p = st.text_input("Scegli Password", type="password", key="r_p")
            if st.button("REGISTRATI"):
                if nuovo_u and nuovo_p:
                    salva_utente(nuovo_u, nuovo_p)
                    st.success("Account creato! Vai su Login")
                else: st.warning("Riempi i campi")

else:
    # --- 6. APP PRINCIPALE (BARRA LATERALE) ---
    with st.sidebar:
        st.markdown(f'<img src="https://cdn-icons-png.flaticon.com/512/4712/4712139.png" width="50" class="logo-img">', unsafe_allow_html=True)
        st.title(f"Ciao {st.session_state.utente_attuale}!")
        scelta = st.radio("Menu", ["💬 Chat", "🧠 Memoria", "⚙️ Settings"])
        st.write("---")
        if st.button("Esci dall'account"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. NAVIGAZIONE SEZIONI ---
    if scelta == "💬 Chat":
        st.title("💬 Chat Intelligente")
        
        # Mostra i messaggi precedenti
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        # Input Chat
        if prompt := st.chat_input("Di' qualcosa..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)
            
            with st.spinner("L'IA sta elaborando..."):
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                st.chat_message("assistant").write(risposta)

    elif scelta == "🧠 Memoria":
        st.title("🧠 Archivio Dati")
        memoria = cervello.carica_memoria(st.session_state.utente_attuale)
        if memoria:
            for k, v in memoria.items():
                with st.expander(f"📍 {k}"):
                    st.write(v)
        else:
            st.info("Non ho ancora memorizzato nulla.")

    elif scelta == "⚙️ Settings":
        st.title("⚙️ Impostazioni")
        st.write(f"Utente attivo: **{st.session_state.utente_attuale}**")
        if st.button("🗑️ Svuota Cronologia Chat"):
            st.session_state.chat_history = []
            st.rerun()
