import json
import os
from groq import Groq
from dotenv import load_dotenv

# --- CONFIGURAZIONE PERCORSI E CHIAVI ---
base_dir = os.path.dirname(__file__)
load_dotenv(os.path.join(base_dir, ".env"))

# Recupero della chiave API
# Su Streamlit Cloud, questa viene letta automaticamente dai "Secrets"
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)
DB_FILE = os.path.join(base_dir, "memoria.json")

# --- GESTIONE MEMORIA ---
def carica_memoria():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salva_memoria(dati):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

# --- ELABORAZIONE ---
def elabora_concetto(username, testo_utente):
    # Il database ora ha il nome dell'utente
    DB_FILE = f"memoria_{username}.json"
    
    def carica_memoria():
        if not os.path.exists(DB_FILE): return {}
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}

    def salva_memoria(dati):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=4, ensure_ascii=False)

    memoria_attuale = carica_memoria()
    
    # Prompt ottimizzato per assistente maschile e mobile
    prompt = f"""
    Sei un assistente virtuale maschile amichevole e sintetico.
    Memoria attuale dell'utente: {json.dumps(memoria_attuale)}
    
    L'utente ti ha scritto: "{testo_utente}"
    
    REGOLE:
    1. Se l'utente ti dà un'informazione da ricordare, rispondi ESATTAMENTE così: SAVE|chiave|valore
    2. Se l'utente fa una domanda, rispondi in modo colloquiale usando la memoria se pertinente.
    3. Sii molto breve (massimo 2 frasi), perfetto per la lettura su smartphone.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6
        )
        
        risposta_ai = completion.choices[0].message.content

        # Logica di salvataggio
        if risposta_ai.startswith("SAVE|"):
            parti = risposta_ai.split("|")
            if len(parti) == 3:
                chiave = parti[1].strip()
                valore = parti[2].strip()
                memoria_attuale[chiave] = valore
                salva_memoria(memoria_attuale)
                return f"Ho memorizzato nel mio database che {chiave} è {valore}."
        
        return risposta_ai

    except Exception as e:
        return f"Errore di connessione con il cervello: {str(e)}"

if __name__ == "__main__":
    # Test rapido da terminale
    print(elabora_concetto())
