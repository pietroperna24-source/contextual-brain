import json
import os
from groq import Groq
from dotenv import load_dotenv

base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def carica_memoria(username):
    file_path = os.path.join(base_dir, f"memoria_{username}.json")
    if not os.path.exists(file_path): return {}
    with open(file_path, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def salva_memoria(username, dati):
    file_path = os.path.join(base_dir, f"memoria_{username}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

def elabora_concetto(username, testo_utente):
    memoria_attuale = carica_memoria(username)
    
    system_prompt = f"""
    Sei un assistente personale intelligente. 
    L'utente attuale è: {username}.
    Memoria attuale: {json.dumps(memoria_attuale)}
    
    REGOLE:
    1. Se l'utente ti dice di ricordare qualcosa, rispondi con: SAVE|chiave|valore
    2. Altrimenti rispondi normalmente.
    3. Sii breve e amichevole.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": testo_utente}],
            temperature=0.6
        )
        risposta_ai = completion.choices[0].message.content

        if "SAVE|" in risposta_ai:
            parti = risposta_ai.split("|")
            if len(parti) >= 3:
                chiave, valore = parti[1].strip(), parti[2].strip()
                memoria_attuale[chiave] = valore
                salva_memoria(username, memoria_attuale)
                # Messaggio chiave per far scattare la notifica nel main.py
                return f"Ho memorizzato una nuova informazione: {chiave} è {valore}."
        
        return risposta_ai
    except Exception as e:
        return f"Errore: {str(e)}"
