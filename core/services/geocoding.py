# services/geocoding.py
import logging
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("geocoding")


class GeocodingService:
    """
    Servizio di geocodifica che utilizza OpenStreetMap Nominatim con:
    - Gestione cache
    - Rate limiting
    - Retry policy
    - Logging GDPR-compliant
    - Timeout configurabile
    """

    def __init__(self):
        self.timeout = settings.GEOCODING_SETTINGS.get("TIMEOUT", 5)
        self.max_retries = settings.GEOCODING_SETTINGS.get("MAX_RETRIES", 2)
        self.cache_timeout = settings.GEOCODING_SETTINGS.get(
            "CACHE_TIMEOUT", 86400
        )  # 24h
        self.user_agent = "CerCollettiva/1.0 (+https://cercollettiva.it)"

    def get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocodifica un indirizzo in coordinate (lat, lon).

        Args:
            address: Indirizzo completo da geocodificare

        Returns:
            Tuple[float, float] | None: Coppia (latitudine, longitudine) o None
            se non trovato
        """
        if not address:
            return None

        # Prima controlla la cache
        cache_key = f"geocoding_{hash(address)}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.debug(
                f"Coordinate trovate in cache per indirizzo hash: {hash(address)}"
            )
            return cached_result

        try:
            # Configura la sessione con retry policy
            session = self._get_session()

            # Prepara la richiesta
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
                "countrycodes": "it",  # Limita a risultati italiani
            }
            headers = {"User-Agent": self.user_agent}

            # Esegui la richiesta
            response = session.get(
                url, params=params, headers=headers, timeout=self.timeout
            )

            # Gestisci la risposta
            if response.status_code == 200:
                results = response.json()
                if results:
                    # Log GDPR-compliant (non logga l'indirizzo completo)
                    logger.info(
                        f"Geocodifica riuscita per indirizzo hash: {hash(address)}"
                    )

                    # Estrai e valida le coordinate
                    coordinates = (float(results[0]["lat"]), float(results[0]["lon"]))

                    # Verifica che le coordinate siano in Italia
                    if self._is_in_italy(coordinates):
                        # Salva in cache
                        cache.set(cache_key, coordinates, self.cache_timeout)
                        return coordinates
                    else:
                        logger.warning(
                            f"Coordinate fuori dall'Italia per indirizzo hash: "
                            f"{hash(address)}"
                        )
                        return None

            logger.warning(
                f"Nessun risultato per geocodifica indirizzo hash: {hash(address)}"
            )
            return None

        except requests.exceptions.Timeout:
            logger.warning(
                f"Timeout durante la geocodifica per indirizzo hash: {hash(address)}"
            )
            return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"Errore di rete durante la geocodifica: {str(e)}")
            return None

        except Exception as e:
            logger.error(f"Errore inaspettato durante la geocodifica: {str(e)}")
            return None

    def _get_session(self) -> requests.Session:
        """Configura e restituisce una sessione HTTP con retry policy"""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def _is_in_italy(self, coordinates: Tuple[float, float]) -> bool:
        """Verifica che le coordinate siano all'interno dell'Italia"""
        lat, lon = coordinates
        return (
            35.0 <= lat <= 48.0  # Latitudine Italia
            and 6.0 <= lon <= 19.0  # Longitudine Italia
        )


# Singleton instance
_geocoding_service = None


def get_geocoding_service() -> GeocodingService:
    """Restituisce l'istanza singleton del servizio di geocodifica"""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service


def get_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """Helper function per ottenere le coordinate da un indirizzo"""
    service = get_geocoding_service()
    return service.get_coordinates(address)
