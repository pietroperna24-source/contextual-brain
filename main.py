import streamlit as st
import cervello
import json
import os

# --- GESTIONE UTENTI ---
UTENTI_FILE = "utenti.json"

def carica_utenti():
    if not os.path.exists(UTENTI_FILE): return {}
    with open(UTENTI_FILE, "r") as f: return json.load(f)

def salva_utente(user, pwd):
    utenti = carica_utenti()
    utenti[user] = pwd
    with open(UTENTI_FILE, "w") as f: json.dump(utenti, f)

# --- INTERFACCIA ---
st.set_page_config(page_title="Cervello Privato", layout="centered")

if 'autenticato' not in st.session_state:
    st.session_state.autenticato = False
    st.session_state.utente_attuale = None

if not st.session_state.autenticato:
    tab1, tab2 = st.tabs(["Login", "Registrazione"])
    
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Accedi"):
            db = carica_utenti()
            if u in db and db[u] == p:
                st.session_state.autenticato = True
                st.session_state.utente_attuale = u
                st.rerun()
            else:
                st.error("Credenziali errate")

    with tab2:
        nuovo_u = st.text_input("Scegli Username")
        nuovo_p = st.text_input("Scegli Password", type="password")
        if st.button("Registrati"):
            db = carica_utenti()
            if nuovo_u in db:
                st.warning("Utente già esistente")
            else:
                salva_utente(nuovo_u, nuovo_p)
                st.success("Registrato! Ora fai il login")

else:
    # --- APP DOPO IL LOGIN ---
    st.sidebar.write(f"👤 Utente: **{st.session_state.utente_attuale}**")
    if st.sidebar.button("Logout"):
        st.session_state.autenticato = False
        st.rerun()

    st.title("🧠 Il tuo Cervello Privato")
    
    input_utente = st.text_input("Cosa vuoi memorizzare?")
    
    if st.button("🚀 ELABORA"):
        if input_utente:
            # Passiamo l'utente al cervello per salvare in file separati
            risposta = cervello.elabora_concetto(st.session_state.utente_attuale, input_utente)
            st.chat_message("assistant").write(risposta)
