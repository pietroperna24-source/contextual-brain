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

# --- 2. JS KILLER (Rimuove badge e icone indesiderate da Codespaces/Streamlit) ---
components.html("""
    <script>
    const cleanUI = () => {
        // Cerca nel documento principale (parent) perché Streamlit è in un iframe
        const elementsToRemove = [
            ".viewerBadge_container__1QSob", 
            ".stDeployButton", 
            "footer", 
            "#MainMenu",
            "header"
        ];
        elementsToRemove.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) el.style.display = 'none';
        });
    };
    // Esecuzione continua per eliminare elementi caricati dinamicamente
    setInterval(cleanUI, 500);
    </script>
""", height=0)

# --- 3. CSS PER ARMONIA E PULIZIA ---
st.markdown("""
    <style>
        /* Nasconde elementi di sistema nel CSS */
        header, footer, .stDeployButton { visibility: hidden !important; height: 0; }
        
        /* Layout Mobile-First */
        .stApp {
            background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        }
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
        }

        /* Titoli e Sottotitoli */
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
            font-size: 0.8rem;
            margin-bottom: 1.5rem;
        }

        /* Bottoni Arrotondati */
        div.stButton > button {
            border-radius: 15px;
            background-color: #6C5CE7;
            color: white;
            font-weight: 600;
            border: none;
            height: 3.5rem;
            width: 100%;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DATI (Database Persistente) ---
def carica_db():
    if not os.path.exists("utenti.json"): return {}
    try:
        with open("utenti.json", "r") as f: return json.load(f)
    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f: 
        json.dump(db, f, indent=4)

# --- 5. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'chat_history': []
    })

# --- 6. INTERFACCIA ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.05, 0.9, 0.05])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Il tuo archivio cognitivo personale</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDI AL SISTEMA"):
                db = carica_db()
                if u in db and db[u].get("pass") == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.session_state.chat_history = db[u].get("history", [])
                    st.rerun()
                else:
                    st.error("Credenziali errate")
        
        with t2:
            nuovo_u = st.text_input("Nuovo Username", key="r_u")
            nuovo_p = st.text_input("Nuova Password", type="password", key="r_p")
            if st.button("CREA ACCOUNT"):
                if nuovo_u and nuovo_p:
                    db = carica_db()
                    db[nuovo_u] = {"pass": nuovo_p, "history": []}
                    salva_db(db)
                    st.success("Account creato! Ora effettua il login.")

else:
    # --- 7. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale}")
        scelta = st.radio("Menu", ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"])
        if st.button("Esci"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. CHAT ---
    if scelta == "💬 Chat":
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            try:
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.chat_message("assistant").write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                # Salvataggio su file JSON
                db = carica_db()
                db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                salva_db(db)
            except Exception as e:
                st.error(f"Errore: {e}")

    # --- 9. MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Memoria Attiva")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"): st.write(v)
        else:
            st.info("La memoria è vuota.")

    # --- 10. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        if st.button("🗑️ Svuota Cronologia"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.rerun()
