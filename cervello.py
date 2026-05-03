import json
import os

MEMORIA_FOLDER = "memoria_utenti"
if not os.path.exists(MEMORIA_FOLDER):
    os.makedirs(MEMORIA_FOLDER)

def carica_memoria(utente):
    file_path = os.path.join(MEMORIA_FOLDER, f"{utente}_brain.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_memoria(utente, dati):
    file_path = os.path.join(MEMORIA_FOLDER, f"{utente}_brain.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)

def elabora_concetto(utente, messaggio):
    memoria = carica_memoria(utente)
    msg_lower = messaggio.lower()

    if "ricorda che" in msg_lower or "memorizza" in msg_lower:
        parti = messaggio.split(" che " if " che " in messaggio else "memorizza ")
        if len(parti) > 1:
            concetto = parti[1].strip()
            chiave = concetto.split()[0].capitalize()
            memoria[chiave] = concetto
            salva_memoria(utente, memoria)
            return f"Ho memorizzato nei tuoi circuiti: '{concetto}'"
    
    for chiave in memoria:
        if chiave.lower() in msg_lower:
            return f"A proposito di {chiave}, ricordo che: {memoria[chiave]}"

    return "Ricevuto. Sto elaborando questa informazione nel tuo contesto attuale."
