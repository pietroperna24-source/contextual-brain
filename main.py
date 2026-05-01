import ascolto
import cervello
import time


def avvia_app():
    print("=== CONTEXTUAL BRAIN V1.0 ===")
    while True:
        # 1. Fase di ascolto
        input_utente = ascolto.attiva_cervello()

        if input_utente:
            # 2. Fase di elaborazione (se abbiamo sentito qualcosa)
            cervello.elabora_concetto()

        print("\nPronto per il prossimo comando... (Ctrl+C per chiudere)")
        time.sleep(1)


if __name__ == "__main__":
    try:
        avvia_app()
    except KeyboardInterrupt:
        print("\nSpegnimento del Cervello. A presto!")