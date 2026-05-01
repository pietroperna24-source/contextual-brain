import json
import os
from groq import Groq
from dotenv import load_dotenv

# Configurazione percorsi
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, ".env"))

# Inizializzazione Client Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def carica_memoria(username):
    file_path = os.path.join(base_dir, f"memoria_{username}.json")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def salva_memoria(username, dati):
    file_path = os.path.join(base_dir, f"memoria_{username}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

def elabora_concetto(username, testo_utente):
    memoria_attuale = carica_memoria(username)
    
    # Prompt di sistema per istruire l'IA
    system_prompt = f"""
    Sei un assistente personale per l'utente {username}.
    Hai accesso a questa memoria: {json.dumps(memoria_attuale)}
    
    ISTRUZIONI:
    1. Se l'utente ti dà un'informazione da ricordare, rispondi con: SAVE|chiave|valore
    2. Altrimenti rispondi normalmente consultando la memoria se necessario.
    3. Sii sintetico e amichevole.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": testo_utente}
            ],
            temperature=0.6
        )
        risposta_ai = completion.choices[0].message.content

        # Gestione del salvataggio
        if "SAVE|" in risposta_ai:
            parti = risposta_ai.split("|")
            if len(parti) >= 3:
                chiave = parti[1].strip()
                valore = parti[2].strip()
                memoria_attuale[chiave] = valore
                salva_memoria(username, memoria_attuale)
                # Questa frase precisa fa scattare il trigger nel main.py
                return f"Ho memorizzato nel tuo database: {chiave} = {valore}."
        
        return risposta_ai

    except Exception as e:
        return f"Errore nel cervello: {str(e)}"
