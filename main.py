import streamlit as st
import cervello  # Assicurati che questo modulo sia presente nel tuo ambiente
import json
import os
import streamlit.components.v1 as components

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual - Admin Edition", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. JS KILLER (UI Cleanup) ---
components.html("""
    <script>
    const cleanUI = () => {
        const elementsToRemove = [".viewerBadge_container__1QSob", ".stDeployButton", "footer", "#MainMenu", "header"];
        elementsToRemove.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(cleanUI, 500);
    </script>
""", height=0)

# --- 3. CSS CUSTOM ---
st.markdown("""
    <style>
        header, footer, .stDeployButton { visibility: hidden !important; height: 0; }
        .stApp { background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); }
        .main-title {
            font-size: 2.5rem; font-weight: 800; text-align: center;
            background: -webkit-linear-gradient(#6C5CE7, #a29bfe);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .sub-title { text-align: center; color: #636E72; font-size: 0.8rem; margin-bottom: 1.5rem; }
        div.stButton > button {
            border-radius: 15px; background-color: #6C5CE7; color: white;
            font-weight: 600; border: none; height: 3.5rem; width: 100%;
        }
        .admin-card {
            padding: 15px; border-radius: 10px; background: white;
            border-left: 5px solid #6C5CE7; margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNZIONI DATI (Gestione Admin) ---
def carica_db():
    if not os.path.exists("utenti.json"):
        # Se il DB non esiste, creiamo un admin di default
        db_iniziale = {
            "admin": {"pass": "admin123", "history": [], "role": "admin"}
        }
        salva_db(db_iniziale)
        return db_iniziale
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
        'role': 'user',
        'chat_history': []
    })

# --- 6. INTERFACCIA ACCESSO ---
if not st.session_state.autenticato:
    st.write("##")
    col_l, col_c, col_r = st.columns([0.1, 0.8, 0.1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 My Contextual Brain</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>Accedi per gestire il tuo archivio cognitivo</p>", unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with t1:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDI AL SISTEMA"):
                db = carica_db()
                if u in db and db[u].get("pass") == p:
                    st.session_state.autenticato = True
                    st.session_state.utente_attuale = u
                    st.session_state.role = db[u].get("role", "user")
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
                    if nuovo_u in db:
                        st.warning("Username già esistente!")
                    else:
                        db[nuovo_u] = {"pass": nuovo_p, "history": [], "role": "user"}
                        salva_db(db)
                        st.success("Account creato! Ora puoi accedere.")

else:
    # --- 7. SIDEBAR (Dinamica in base al ruolo) ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale.upper()}")
        st.info(f"Ruolo: {st.session_state.role}")
        
        menu_options = ["💬 Chat", "🧠 Memoria", "⚙️ Impostazioni"]
        if st.session_state.role == "admin":
            menu_options.insert(0, "🛡️ Pannello Admin")
            
        scelta = st.radio("Menu", menu_options)
        
        st.write("---")
        if st.button("Esci"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 8. LOGICA AMMINISTRATORE ---
    if scelta == "🛡️ Pannello Admin":
        st.title("🛡️ Amministrazione Sistema")
        db = carica_db()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Utenti Totali", len(db))
        col2.metric("Chat Totali", sum(len(d.get("history", [])) for d in db.values()))
        col3.metric("Spazio", "JSON DB")

        st.subheader("Gestione Utenti")
        for user, data in db.items():
            with st.container():
                st.markdown(f"""
                <div class='admin-card'>
                    <strong>Utente:</strong> {user} | <strong>Ruolo:</strong> {data['role']} | 
                    <strong>Messaggi:</strong> {len(data['history'])}
                </div>
                """, unsafe_allow_html=True)
                
                # Non permettere all'admin di eliminare se stesso facilmente
                if user != st.session_state.utente_attuale:
                    if st.button(f"Elimina {user}", key=f"del_{user}"):
                        del db[user]
                        salva_db(db)
                        st.rerun()

    # --- 9. CHAT ---
    elif scelta == "💬 Chat":
        for msg in st.session_state.chat_history:
            st.chat_message(msg["role"]).write(msg["content"])

        if prompt := st.chat_input("Scrivi qui..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.chat_message("user").write(prompt)

            try:
                risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                st.chat_message("assistant").write(risposta)
                st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                
                db = carica_db()
                db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                salva_db(db)
            except Exception as e:
                st.error(f"Errore: {e}")

    # --- 10. MEMORIA ---
    elif scelta == "🧠 Memoria":
        st.title("🧠 Memoria Attiva")
        mem = cervello.carica_memoria(st.session_state.utente_attuale)
        if mem:
            for k, v in mem.items():
                with st.expander(f"📌 {k}"): st.write(v)
        else:
            st.info("La memoria è vuota.")

    # --- 11. IMPOSTAZIONI ---
    elif scelta == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni Profilo")
        if st.button("🗑️ Svuota la mia Cronologia"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Cronologia pulita!")
            st.rerun()
