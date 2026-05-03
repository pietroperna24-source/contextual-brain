FROM python:3.11-slim

# Installazione dipendenze di sistema per PyAudio e strumenti di compilazione
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e installazione requisiti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del resto del codice
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "main.py"]
