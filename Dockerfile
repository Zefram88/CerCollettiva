# Dockerfile per CerCollettiva
FROM python:3.11-slim

# Metadati
LABEL maintainer="CerCollettiva Team <team@cercollettiva.it>"
LABEL description="CerCollettiva - Sistema di gestione Comunità Energetiche Rinnovabili"
LABEL version="1.0.0"

# Variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crea utente non-root
RUN groupadd -r cercollettiva && useradd -r -g cercollettiva cercollettiva

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY . .

# Crea directory necessarie
RUN mkdir -p /app/logs /app/media /app/staticfiles && \
    chown -R cercollettiva:cercollettiva /app

# Cambia utente
USER cercollettiva

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/monitoring/health/ || exit 1

# Comando di default
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "cercollettiva.wsgi:application"]
