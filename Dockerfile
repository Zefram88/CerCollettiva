# Dockerfile per CerCollettiva
FROM python:3.11-slim

# Metadati
LABEL maintainer="CerCollettiva Team <team@cercollettiva.it>"
LABEL description="CerCollettiva - Sistema di gestione Comunità Energetiche Rinnovabili"
LABEL version="1.0.0"

# Variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Crea utente non-root
RUN groupadd -r cercollettiva && useradd -r -g cercollettiva cercollettiva

# Configura sudo per cercollettiva
RUN echo "cercollettiva ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Imposta directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
# Abilita cache pip con BuildKit per velocizzare build successivi
# syntax: docker/dockerfile:1.4
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copia codice sorgente
# Copia solo il minimo indispensabile per invalidare cache sui cambi codice
COPY . .

# Crea symlink per supportare bind mount in development
RUN ln -sf /app/src/cercollettiva /app/cercollettiva || true

# Copia script di entrypoint
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY scripts/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh

# Crea directory necessarie
RUN mkdir -p /app/logs /app/media /app/staticfiles && \
    chown -R cercollettiva:cercollettiva /app

# Cambia utente
USER cercollettiva

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/monitoring/health/ || exit 1

# Entrypoint per setup automatico
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Comando di default (Produzione)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "cercollettiva.wsgi:application"]
