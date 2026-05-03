import json
import streamlit as st
from groq import Groq

# Usa st.secrets invece di os.getenv per Streamlit Cloud
try:
    api_key = st.secrets["groq"]["api_key"]
    client = Groq(api_key=api_key)
    GROQ_ATTIVO = True
except Exception as e:
    client = None
    GROQ_ATTIVO = False
    st.warning(f"Groq non configurato: {e}")

def elabora_concetto(username, testo_utente, memoria_dict=None):
    if not GROQ_ATTIVO:
        return "Errore: GROQ_API_KEY non configurata. Vai su Settings → Secrets su Streamlit Cloud e aggiungi [groq] api_key = 'gsk_...'"

    memoria = memoria_dict or {}

    system_prompt = f"""
    Sei un assistente personale per l'utente {username}.
    Hai accesso a questa memoria: {json.dumps(memoria, ensure_ascii=False)}

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
        return completion.choices[0].message.content
    except Exception as e:
        return f"Errore Groq: {str(e)}"
