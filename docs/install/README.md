# Installazione CerCollettiva

## Scelta Metodo Installazione

### 🐳 Docker (Raccomandato)
- **Sviluppo:** `docker-compose up -d`
- **Produzione:** `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- **Vantaggi:** Ambiente isolato, configurazione automatica, backup integrato

### 🖥️ Installazione Nativa
- **Sviluppo:** `./docs/install/install-dev.sh` (da creare)
- **Produzione:** `./docs/install/install-prod.sh` o `./docs/install/install-prod-v2.sh`
- **WSL:** `./docs/install/install-wsl.sh`
- **Vantaggi:** Controllo completo, performance native

## Script Disponibili

| Script | Descrizione | Uso |
|--------|-------------|-----|
| `install-prod.sh` | Installazione produzione v1.2 | Server Linux standard |
| `install-prod-v2.sh` | Installazione produzione v2.0 | Server Linux con Redis |
| `install-wsl.sh` | Installazione WSL | Windows Subsystem for Linux |
| `uninstall.sh` | Disinstallazione completa | Cleanup sistema |

## Quando Usare Cosa

| Scenario | Metodo | Motivo |
|----------|--------|--------|
| Sviluppo rapido | Docker | Auto-reload, configurazione automatica |
| Sviluppo avanzato | Nativo | Debugging profondo, personalizzazioni |
| Produzione cloud | Docker | Scalabilità, orchestrazione |
| Produzione VPS | Nativo | Controllo risorse, performance |
| Sviluppo Windows | WSL | Ambiente Linux su Windows |

## Prerequisiti

### Docker
- Docker Desktop (Windows/Mac) o Docker Engine (Linux)
- Docker Compose v2.0+

### Nativo
- Ubuntu 20.04+ / Debian 11+
- Python 3.9+
- PostgreSQL 13+
- Nginx
- 2GB RAM, 10GB spazio disco

## Quick Start

### Docker
```bash
# Sviluppo
docker-compose up -d

# Produzione
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Nativo
```bash
# Produzione
chmod +x docs/install/install-prod.sh
./docs/install/install-prod.sh

# WSL
chmod +x docs/install/install-wsl.sh
./docs/install/install-wsl.sh
```

## Configurazione

### Variabili Ambiente
Copia `env.example` in `.env` e configura:
- `DEBUG=True/False`
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `SECRET_KEY`
- `ALLOWED_HOSTS`

### SSL/HTTPS
- **Docker:** Automatico con Let's Encrypt
- **Nativo:** Usa `scripts/setup-letsencrypt.sh`

## Troubleshooting

### Docker
- Verifica: `docker-compose logs`
- Riavvia: `docker-compose restart`
- Reset: `docker-compose down -v && docker-compose up -d`

### Nativo
- Log: `/var/log/nginx/cercollettiva_error.log`
- Servizi: `systemctl status gunicorn nginx postgresql`
- Riavvia: `systemctl restart gunicorn nginx`

## Supporto

- **Documentazione:** `docs/guides/`
- **API:** `docs/api/reference.md`
- **Issues:** GitHub Issues
