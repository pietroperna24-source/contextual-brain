import speech_recognition as sr


def attiva_cervello():
    rec = sr.Recognizer()

    with sr.Microphone() as source:
        print("\n--- [CERVELLO PRONTO] ---")
        print("Dimmi cosa vuoi ricordare o chiedimi qualcosa...")

        # Elimina i rumori di fondo per una trascrizione precisa
        rec.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = rec.listen(source, timeout=5)
            print("Elaborazione in corso...")

            # Trasformazione Audio -> Testo
            testo = rec.recognize_google(audio, language="it-IT")
            print(f"\nVOCE RILEVATA: '{testo}'")

            # Salvataggio per il passo successivo
            with open("input_recente.txt", "w", encoding="utf-8") as f:
                f.write(testo)

            return testo

        except sr.WaitTimeoutError:
            print("Non ho sentito nulla. Sei ancora lì?")
        except sr.UnknownValueError:
            print("Suono rilevato, ma non sono riuscito a interpretare le parole.")
        except Exception as e:
            print(f"Errore tecnico: {e}")


if __name__ == "__main__":
    attiva_cervello()