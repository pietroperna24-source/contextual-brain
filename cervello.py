import json
import os
from groq import Groq
from dotenv import load_dotenv

# --- CONFIGURAZIONE AMBIENTE ---
base_dir = os.path.dirname(__file__)
# Carica le variabili dal file .env (solo per test locale)
load_dotenv(os.path.join(base_dir, ".env"))

# Recupero della chiave API (da .env in locale o Secrets su Streamlit)
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

def carica_memoria(username):
    """Carica il database JSON specifico per l'utente."""
    file_memoria = os.path.join(base_dir, f"memoria_{username}.json")
    if not os.path.exists(file_memoria):
        return {}
    with open(file_memoria, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salva_memoria(username, dati):
    """Salva i dati nel database JSON specifico per l'utente."""
    file_memoria = os.path.join(base_dir, f"memoria_{username}.json")
    with open(file_memoria, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

def elabora_concetto(username, testo_utente):
    """
    Invia il testo a Groq, analizza se c'è qualcosa da memorizzare
    e restituisce la risposta testuale per l'interfaccia.
    """
    
    # Recuperiamo la memoria storica di questo specifico utente
    memoria_attuale = carica_memoria(username)
    
    # Istruzioni di sistema (Prompt) per l'IA
    system_prompt = f"""
    Sei un assistente virtuale maschile chiamato 'Cervello Contestuale'. 
    Il tuo compito è aiutare l'utente {username} a ricordare informazioni e rispondere alle sue domande.
    
    MEMORIA ATTUALE DELL'UTENTE:
    {json.dumps(memoria_attuale)}
    
    REGOLE DI RISPOSTA:
    1. Se l'utente ti dà un'info da ricordare (es: 'Ricorda che...'), rispondi iniziando con 'SAVE|chiave|valore'.
    2. Se l'utente fa una domanda, consulta la memoria fornita sopra.
    3. Sii amichevole, usa un tono maschile e sii molto sintetico (massimo 2-3 frasi).
    4. Non menzionare mai i formati tecnici come JSON o 'SAVE|' all'utente finale.
    """

    try:
        # Chiamata a Groq (Llama 3.3)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": testo_utente}
            ],
            temperature=0.6,
            max_tokens=500
        )
        
        risposta_ai = completion.choices[0].message.content

        # --- LOGICA DI SALVATAGGIO IN MEMORIA ---
        if "SAVE|" in risposta_ai:
            # Estraiamo i dati dal formato SAVE|chiave|valore
            parti = risposta_ai.split("|")
            if len(parti) >= 3:
                chiave = parti[1].strip()
                valore = parti[2].strip()
                
                # Aggiorniamo il JSON dell'utente
                memoria_attuale[chiave] = valore
                salva_memoria(username, memoria_attuale)
                
                return f"Ho recepito e memorizzato: **{chiave}** è **{valore}**. Cos'altro posso fare per te?"
        
        # Risposta standard se non c'è nulla da salvare
        return risposta_ai

    except Exception as e:
        return f"Scusa {username}, ho avuto un piccolo corto circuito tecnico: {str(e)}"

# Se il file viene lanciato da solo (test)
if __name__ == "__main__":
    test_user = "Pietro"
    test_input = "Ricorda che la mia pizza preferita è la Diavola"
    print(f"TEST LOGICA: {elabora_concetto(test_user, test_input)}")
