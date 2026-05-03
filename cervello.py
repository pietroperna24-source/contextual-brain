import json
import streamlit as st
from groq import Groq

# --- 1. INIZIALIZZA GROQ USANDO st.secrets ---
try:
    api_key = st.secrets["groq"]["api_key"]
    client = Groq(api_key=api_key)
    GROQ_ATTIVO = True
except Exception:
    client = None
    GROQ_ATTIVO = False

# --- 2. MEMORIA SU DB INVECE CHE FILE ---
# Usiamo il DB di app.py invece dei.json che si cancellano su Cloud
def carica_memoria(username):
    """Legge la memoria dal database invece che da file"""
    from app import get_user # Import circolare safe perché chiamato solo dentro funzione
    user = get_user(username)
    if user and user.get("history"):
        # Usiamo l'history come memoria temporanea
        # Oppure aggiungi una colonna 'memoria' alla tabella User
        try:
            return json.loads(user["history"][0]["content"]) if user["history"] else {}
        except:
            return {}
    return {}

def salva_memoria(username, dati):
    """Su Streamlit Cloud non salviamo su file. La memoria va nel DB."""
    # Per ora la teniamo solo in sessione. Se vuoi persistenza vera,
    # aggiungi una colonna 'memoria' TEXT alla tabella User in app.py
    st.session_state[f"memoria_{username}"] = dati
    return True

# Versione memoria solo in sessione per evitare file su Cloud
def carica_memoria_session(username):
    return st.session_state.get(f"memoria_{username}", {})

def salva_memoria_session(username, dati):
    st.session_state[f"memoria_{username}"] = dati

def elabora_concetto(username, testo_utente):
    if not GROQ_ATTIVO:
        return "Errore: GROQ_API_KEY non configurata. Vai su Settings → Secrets e aggiungi [groq] api_key = 'gsk_...'"

    memoria_attuale = carica_memoria_session(username)

    system_prompt = f"""
    Sei un assistente personale per l'utente {username}.
    Hai accesso a questa memoria: {json.dumps(memoria_attuale, ensure_ascii=False)}

    ISTRUZIONI:
    1. Se l'utente ti dà un'informazione da ricordare, rispondi con: SAVE|chiave|valore
    2. Altrimenti rispondi normalmente consultando la memoria se necessario.
    3. Sii sintetico e amichevole. Rispondi in italiano.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": testo_utente}
            ],
            temperature=0.6,
            max_tokens=800
        )
        risposta_ai = completion.choices[0].message.content

        # Gestione del salvataggio in sessione
        if "SAVE|" in risposta_ai:
            parti = risposta_ai.split("|")
            if len(parti) >= 3:
                chiave = parti[1].strip()
                valore = parti[2].strip()
                memoria_attuale[chiave] = valore
                salva_memoria_session(username, memoria_attuale)
                return f"Ho memorizzato: {chiave} = {valore}"

        return risposta_ai

    except Exception as e:
        return f"Errore Groq: {str(e)}"
