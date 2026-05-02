import streamlit as st
import json
import os
import streamlit.components.v1 as components

# Prova a importare il modulo cervello, con fallback se manca
try:
    import cervello
except ImportError:
    cervello = None

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Cervello Contextual PRO v3",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UI ENHANCEMENT (JS & CSS) ---
components.html("""
    <script>
    const cleanUI = () => {
        const elementsToRemove = [".viewerBadge_container__1QSob", ".stDeployButton", "footer", "header"];
        elementsToRemove.forEach(selector => {
            const el = window.parent.document.querySelector(selector);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(cleanUI, 500);
    </script>
""", height=0)

st.markdown("""
    <style>
        .stApp { background-color: #F4F7F9; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #DDE4E8; }
        
        /* Box Messaggi */
        .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
        
        /* Bottoni Custom */
        div.stButton > button {
            border-radius: 8px;
            transition: all 0.2s ease;
            border: 1px solid #6C5CE7;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(108, 92, 231, 0.2);
        }
        
        /* Toolbar Superiore */
        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 20px;
            background: white;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. CORE DATABASE ENGINE ---
DB_FILE = "utenti.json"

def carica_db():
    if not os.path.exists(DB_FILE):
        db = {"admin": {"pass": "admin123", "history": [], "role": "admin"}}
        salva_db(db)
        return db
    with open(DB_FILE, "r") as f:
        return json.load(f)

def salva_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

# --- 4. SESSION STATE INITIALIZATION ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': [],
        'pagina': 'chat'
    })

# --- 5. SISTEMA DI ACCESSO ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.write("##")
        st.markdown("<h1 style='text-align: center;'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        tab_l, tab_r = st.tabs(["🔐 Login", "📝 Registrazione"])
        
        with tab_l:
            u = st.text_input("Username", placeholder="admin")
            p = st.text_input("Password", type="password", placeholder="admin123")
            if st.button("ACCEDI ALL'APP", use_container_width=True):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True,
                        'utente_attuale': u,
                        'role': db[u].get("role", "user"),
                        'chat_history': db[u].get("history", [])
                    })
                    st.rerun()
                else:
                    st.error("Accesso negato. Riprova.")
                    
        with tab_r:
            nu = st.text_input("Nuovo User")
            np = st.text_input("Nuova Pass", type="password")
            if st.button("CREA ACCOUNT", use_container_width=True):
                if nu and np:
                    db = carica_db()
                    if nu not in db:
                        db[nu] = {"pass": np, "history": [], "role": "user"}
                        salva_db(db)
                        st.success("Account creato con successo!")
                    else: st.warning("Utente già esistente.")

else:
    # --- 6. SIDEBAR & CATALOGO ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.utente_attuale.upper()}")
        st.caption(f"Status: {st.session_state.role.upper()}")
        st.write("---")
        
        # Navigazione Rapida
        if st.button("💬 Chat AI", use_container_width=True):
            st.session_state.pagina = "chat"
            st.rerun()
            
        if st.button("📂 Catalogo Memoria", use_container_width=True):
            st.session_state.pagina = "memoria"
            st.rerun()
            
        if st.session_state.role == "admin":
            if st.button("🛡️ Pannello Admin", use_container_width=True):
                st.session_state.pagina = "admin"
                st.rerun()
        
        st.write("---")
        if st.button("⚙️ Impostazioni", use_container_width=True):
            st.session_state.pagina = "impostazioni"
            st.rerun()
            
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. TOOLBAR SUPERIORE (Tasto Indietro Dinamico) ---
    col_tit, col_back = st.columns([0.8, 0.2])
    with col_back:
        if st.session_state.pagina != "chat":
            if st.button("⬅️ INDIETRO", use_container_width=True):
                st.session_state.pagina = "chat"
                st.rerun()

    # --- 8. LOGICA PAGINE ---

    # --- PAGINA ADMIN ---
    if st.session_state.pagina == "admin" and st.session_state.role == "admin":
        st.title("🛡️ Amministrazione")
        db = carica_db()
        
        st.subheader("Database Utenti")
        for u_id, u_data in db.items():
            with st.expander(f"Utente: {u_id}"):
                st.write(f"Ruolo: {u_data['role']}")
                st.write(f"Messaggi in memoria: {len(u_data['history'])}")
                if u_id != "admin":
                    if st.button(f"Elimina Account {u_id}", key=f"del_{u_id}"):
                        del db[u_id]
                        salva_db(db)
                        st.rerun()

    # --- PAGINA MEMORIA ---
    elif st.session_state.pagina == "memoria":
        st.title("📂 Il tuo Catalogo")
        if cervello:
            try:
                mem = cervello.carica_memoria(st.session_state.utente_attuale)
                if mem:
                    for k, v in mem.items():
                        st.info(f"**{k}**: {v}")
                else: st.warning("La tua memoria è vuota. Inizia a chattare!")
            except: st.error("Errore nel recupero dati.")
        else:
            st.error("Modulo 'cervello' non rilevato.")

    # --- PAGINA IMPOSTAZIONI ---
    elif st.session_state.pagina == "impostazioni":
        st.title("⚙️ Impostazioni")
        if st.button("🗑️ Reset Cronologia Chat"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Tabula rasa effettuata.")

    # --- PAGINA CHAT ---
    else:
        st.markdown("<h2 style='text-align: center;'>🧠 Brain Interface</h2>", unsafe_allow_html=True)
        
        # Display Chat
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        # Chat Input
        if prompt := st.chat_input("Digita un comando o un'informazione..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)

            if cervello:
                try:
                    res = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    with st.chat_message("assistant"): st.write(res)
                    st.session_state.chat_history.append({"role": "assistant", "content": res})
                    
                    # Salvataggio immediato
                    db = carica_db()
                    db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                    salva_db(db)
                except Exception as e:
                    st.error(f"Errore elaborazione: {e}")
            else:
                st.warning("Sistema di IA non collegato (Modulo 'cervello' mancante).")    except: return {}

def salva_db(db):
    with open("utenti.json", "w") as f:
        json.dump(db, f, indent=4)

# --- 4. SESSION STATE ---
if 'autenticato' not in st.session_state:
    st.session_state.update({
        'autenticato': False,
        'utente_attuale': None,
        'role': 'user',
        'chat_history': []
    })

# --- 5. LOGICA DI ACCESSO ---
if not st.session_state.autenticato:
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 class='main-title'>🧠 Contextual Brain</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔐 Login", "📝 Registrati"])
        
        with tab_log:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDI"):
                db = carica_db()
                if u in db and db[u]["pass"] == p:
                    st.session_state.update({
                        'autenticato': True,
                        'utente_attuale': u,
                        'role': db[u].get("role", "user"),
                        'chat_history': db[u].get("history", [])
                    })
                    st.rerun()
                else:
                    st.error("Credenziali non valide")
        
        with tab_reg:
            new_u = st.text_input("Nuovo Username")
            new_p = st.text_input("Nuova Password", type="password")
            if st.button("CREA ACCOUNT"):
                if new_u and new_p:
                    db = carica_db()
                    if new_u not in db:
                        db[new_u] = {"pass": new_p, "history": [], "role": "user"}
                        salva_db(db)
                        st.success("Registrato! Ora fai il login.")
                    else: st.warning("Username occupato.")

else:
    # --- 6. SIDEBAR: IL TUO CATALOGO ---
    with st.sidebar:
        st.markdown(f"### 👋 Benvenuto, {st.session_state.utente_attuale}")
        st.caption(f"Ruolo: {st.session_state.role.capitalize()}")
        st.write("---")

        # MENU DI NAVIGAZIONE
        menu = st.selectbox("Vai a:", ["💬 Chat AI", "⚙️ Impostazioni"])
        
        if st.session_state.role == "admin":
            if st.button("🛡️ Pannello Amministratore", use_container_width=True):
                st.session_state.page = "admin"
            else: st.session_state.page = "app"
        else:
            st.session_state.page = "app"

        st.write("---")
        
        # CATALOGO MEMORIE (Visualizzazione rapida)
        st.markdown("#### 📚 Catalogo Memorie")
        try:
            memorie = cervello.carica_memoria(st.session_state.utente_attuale)
            if memorie:
                for chiave in list(memorie.keys())[:5]: # Mostra le ultime 5
                    st.markdown(f"<div class='memoria-item'>{chiave}</div>", unsafe_allow_html=True)
                if st.button("Vedi tutte le memorie"):
                    st.session_state.view_mem = True
            else:
                st.info("Nessun dato salvato.")
        except:
            st.caption("Modulo memoria non disponibile.")

        st.write("---")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.autenticato = False
            st.rerun()

    # --- 7. CONTENUTO PRINCIPALE ---
    
    # PAGINA AMMINISTRATORE
    if st.session_state.role == "admin" and st.session_state.get("page") == "admin":
        st.title("🛡️ Dashboard Amministrazione")
        db = carica_db()
        
        col1, col2 = st.columns(2)
        col1.metric("Utenti Registrati", len(db))
        col2.metric("Attività Database", "Online")

        st.write("### Lista Utenti")
        for user, info in db.items():
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.write(f"**{user}**")
            c2.write(f"Ruolo: {info['role']}")
            if user != "admin":
                if c3.button("Elimina", key=f"del_{user}"):
                    del db[user]
                    salva_db(db)
                    st.rerun()

    # PAGINA CHAT / MEMORIA (APP PRINCIPALE)
    elif menu == "💬 Chat AI":
        st.markdown(f"<h2 style='text-align: center;'>🧠 {st.session_state.utente_attuale.capitalize()}'s Brain</h2>", unsafe_allow_html=True)
        
        # Visualizzazione Memoria se cliccato "Vedi tutte"
        if st.session_state.get("view_mem"):
            with st.expander("📂 Archivio Completo Memorie", expanded=True):
                full_mem = cervello.carica_memoria(st.session_state.utente_attuale)
                for k, v in full_mem.items():
                    st.write(f"**{k}**: {v}")
                if st.button("Chiudi Archivio"):
                    st.session_state.view_mem = False
                    st.rerun()

        # Chat interface
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        if prompt := st.chat_input("Chiedi qualcosa o memorizza un concetto..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    risposta = cervello.elabora_concetto(st.session_state.utente_attuale, prompt)
                    st.markdown(risposta)
                    st.session_state.chat_history.append({"role": "assistant", "content": risposta})
                    
                    # Salva cronologia
                    db = carica_db()
                    db[st.session_state.utente_attuale]["history"] = st.session_state.chat_history
                    salva_db(db)
                except Exception as e:
                    st.error(f"Errore: {e}")

    # PAGINA IMPOSTAZIONI
    elif menu == "⚙️ Impostazioni":
        st.title("⚙️ Impostazioni")
        st.subheader("Gestione Dati Personali")
        if st.button("🗑️ Cancella tutta la cronologia chat"):
            st.session_state.chat_history = []
            db = carica_db()
            db[st.session_state.utente_attuale]["history"] = []
            salva_db(db)
            st.success("Cronologia eliminata!")
            st.rerun()
        
        st.write("---")
        st.caption("Versione Contextual Brain 2.0 - Powered by Cervello Engine")
