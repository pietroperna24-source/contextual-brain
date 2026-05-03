import json
import os

# Cartella dove verranno salvati i ricordi degli utenti
MEMORIA_FOLDER = "memoria_utenti"
if not os.path.exists(MEMORIA_FOLDER):
    os.makedirs(MEMORIA_FOLDER)

def carica_memoria(utente):
    """Carica il dizionario dei ricordi dal file JSON dell'utente."""
    file_path = os.path.join(MEMORIA_FOLDER, f"{utente}_brain.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_memoria(utente, dati):
    """Salva i ricordi su disco."""
    file_path = os.path.join(MEMORIA_FOLDER, f"{utente}_brain.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_color=False)

def elabora_concetto(utente, messaggio):
    """
    Logica principale: analizza il messaggio e decide se rispondere 
    o memorizzare qualcosa.
    """
    memoria = carica_memoria(utente)
    msg_lower = messaggio.lower()

    # Esempio di logica di apprendimento semplice
    # Se l'utente dice: "Ricorda che la mia chiave è 1234"
    if "ricorda che" in msg_lower or "memorizza" in msg_lower:
        parti = messaggio.split(" che " if " che " in messaggio else "memorizza ")
        if len(parti) > 1:
            concetto = parti[1].strip()
            # Chiave fittizia basata sulla prima parola del concetto
            chiave = concetto.split()[0].capitalize()
            memoria[chiave] = concetto
            salva_memoria(utente, memoria)
            return f"Ho memorizzato nei tuoi circuiti: '{concetto}'"
    
    # Esempio di recupero memoria
    for chiave in memoria:
        if chiave.lower() in msg_lower:
            return f"A proposito di {chiave}, ricordo che: {memoria[chiave]}"

    # Risposta generica se non ci sono comandi di memoria
    return "Ricevuto. Sto elaborando questa informazione nel tuo contesto attuale."
