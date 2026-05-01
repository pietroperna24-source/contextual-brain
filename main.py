import streamlit as st
import cervello
import os

st.set_page_config(page_title="Cervello Contextual", page_icon="🧠")

st.title("🧠 Il mio Assistente Personale")

# Creiamo un'area di testo invece dell'ascolto vocale
input_testo = st.text_input("Scrivi qualcosa all'IA:", placeholder="Es: Ricorda che mi piace il caffè")

if st.button("Invia al Cervello"):
    if input_testo:
        # Salviamo l'input in un file temporaneo così il tuo vecchio cervello.py lo legge
        with open("input_recente.txt", "w", encoding="utf-8") as f:
            f.write(input_testo)
        
        with st.spinner("L'IA sta elaborando..."):
            # Chiamiamo la logica del cervello
            cervello.elabora_concetto()
            
            # Leggiamo la risposta se l'abbiamo salvata in un log o la mostriamo
            st.success("Comando elaborato!")
            st.info("Nota: Sul web la risposta vocale è disattivata. Controlla la memoria.json su GitHub.")
    else:
        st.warning("Inserisci del testo prima di premere il bottone.")
