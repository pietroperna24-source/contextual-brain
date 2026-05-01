import json
import os

DB_FILE = "memoria.json"


def carica_memoria():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def salva_memoria(dati):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=4, ensure_ascii=False)


def elabora_concetto():
    if not os.path.exists("input_recente.txt"):
        return

    with open("input_recente.txt", "r", encoding="utf-8") as f:
        testo = f.read().lower()

    memoria = carica_memoria()

    # Logica di salvataggio: "Ricorda che..."
    if "ricorda" in testo:
        info = testo.replace("ricorda che", "").replace("ricorda", "").strip()
        # Usiamo la prima parola dell'info come chiave
        parole = info.split()
        if parole:
            chiave = parole[0]
            memoria[chiave] = info
            salva_memoria(memoria)
            print(f"✅ Memoria aggiornata: {info}")

    # Logica di ricerca
    else:
        trovato = False
        for chiave in memoria:
            if chiave in testo:
                print(f"🔍 Ho trovato nei miei ricordi: {memoria[chiave]}")
                trovato = True
        if not trovato:
            print("❌ Non ho informazioni su questo.")