#!/usr/bin/env python3
"""
GSE POD Resolver - Python Module
================================

Modulo Python per la risoluzione di POD (Point of Delivery) tramite servizi GSE diretti.
Fornisce informazioni su Cabina Primaria, Fornitore, Regioni, Province e Comuni associati.

Author: GSE POD Resolver
Version: 1.0.0
License: MIT

USAGE PRINCIPALE:
    from gse_pod_resolver import GSEPodResolver, PODResult
    
    # Metodo 1: Utilizzo diretto
    resolver = GSEPodResolver(timeout=45)
    result = resolver.resolve_pod("IT001E12345678")
    print(f"Fornitore: {result.fornitore}")
    resolver.close()
    
    # Metodo 2: Context manager (raccomandato)
    with GSEPodResolver() as resolver:
        result = resolver.resolve_pod("IT001E12345678")
        print(f"Regioni: {result.regioni}")
        print(f"Province: {result.province}")
        print(f"Comuni: {result.comuni}")
    
    # Metodo 3: Accesso diretto alle mappe ISTAT
    resolver = GSEPodResolver()
    print(f"Regione 5: {resolver.regioni_map[5]}")      # "Veneto"
    print(f"Provincia 27: {resolver.province_map[27]}")  # "Venezia"
    resolver.close()

METODI PUBBLICI DISPONIBILI:
    - __init__(timeout: int = 30): Inizializza il risolutore
    - resolve_pod(pod_code: str) -> PODResult: Metodo principale
    - close(): Chiude la sessione HTTP
    - __enter__() / __exit__(): Supporto context manager

ATTRIBUTI PUBBLICI:
    - base_url: URL base servizi GSE
    - session: Sessione HTTP riutilizzabile
    - regioni_map: Mappa codici regione → nomi
    - province_map: Mappa codici provincia → nomi

ESEMPI AVANZATI:
    # Gestione errori completa
    try:
        with GSEPodResolver() as resolver:
            result = resolver.resolve_pod("IT001E12345678")
            print(f"✅ POD: {result.pod}")
            print(f"✅ Cabina Primaria: {result.cabina_primaria}")
            print(f"✅ Fornitore: {result.fornitore}")
            print(f"✅ Regioni: {result.regioni}")
            print(f"✅ Province: {result.province}")
            print(f"✅ Comuni: {result.comuni}")
    except ValueError as e:
        print(f"❌ POD non valido: {e}")
    except RuntimeError as e:
        print(f"❌ Errore di risoluzione: {e}")
    
    # Validazione formato POD
    resolver = GSEPodResolver()
    if resolver._validate_pod_format("IT001E12345678"):
        result = resolver.resolve_pod("IT001E12345678")
    resolver.close()
    
    # Timeout personalizzato
    resolver = GSEPodResolver(timeout=60)  # 60 secondi
    result = resolver.resolve_pod("IT001E12345678")
    resolver.close()
"""

import requests
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PODResult:
    """
    Risultato della risoluzione di un POD.
    
    Attributes:
        pod (str): Codice POD originale
        cabina_primaria (str): Codice della cabina primaria
        fornitore (str): Nome del fornitore del servizio
        regioni (str): Elenco delle regioni (comma-separated)
        province (str): Elenco delle province (comma-separated)
        comuni (str): Elenco dei comuni della cabina primaria (comma-separated)
    """
    pod: str
    cabina_primaria: str
    fornitore: str
    regioni: str
    province: str
    comuni: str


class GSEPodResolver:
    """
    Risolutore di POD tramite servizi GSE ArcGIS REST API.
    
    Questa classe fornisce metodi per:
    - Trovare la cabina primaria associata a un POD
    - Ottenere informazioni geografiche (regioni, province, comuni)
    - Tradurre codici ISTAT in nomi leggibili
    
    Attributes:
        base_url (str): URL base dei servizi GSE
        session (requests.Session): Sessione HTTP riutilizzabile
    """
    
    def __init__(self, timeout: int = 30):
        """
        Inizializza il risolutore GSE.
        
        Args:
            timeout (int): Timeout per le richieste HTTP in secondi
        """
        self.base_url = "https://mappe.gse.it/srvf/rest/services"
        self.session = requests.Session()
        self.session.timeout = timeout
        
        # Mappe per la traduzione dei codici ISTAT
        self._init_istat_maps()
        
        logger.info("GSEPodResolver inizializzato")
    
    def _init_istat_maps(self):
        """Inizializza le mappe per la traduzione dei codici ISTAT."""
        
        # Mappa regioni: COD_REG -> Nome Regione
        self.regioni_map = {
            '01': 'Piemonte', '02': 'Valle d\'Aosta', '03': 'Lombardia', '04': 'Trentino-Alto Adige',
            '05': 'Veneto', '06': 'Friuli-Venezia Giulia', '07': 'Liguria', '08': 'Emilia-Romagna',
            '09': 'Toscana', '10': 'Umbria', '11': 'Marche', '12': 'Lazio', '13': 'Abruzzo',
            '14': 'Molise', '15': 'Campania', '16': 'Puglia', '17': 'Basilicata',
            '18': 'Calabria', '19': 'Sicilia', '20': 'Sardegna',
            # Supporto per numeri interi (come restituisce GSE)
            1: 'Piemonte', 2: 'Valle d\'Aosta', 3: 'Lombardia', 4: 'Trentino-Alto Adige',
            5: 'Veneto', 6: 'Friuli-Venezia Giulia', 7: 'Liguria', 8: 'Emilia-Romagna',
            9: 'Toscana', 10: 'Umbria', 11: 'Marche', 12: 'Lazio', 13: 'Abruzzo',
            14: 'Molise', 15: 'Campania', 16: 'Puglia', 17: 'Basilicata',
            18: 'Calabria', 19: 'Sicilia', 20: 'Sardegna'
        }
        
        # Mappa province: COD_PROV -> Nome Provincia
        self.province_map = {
            '001': 'Torino', '002': 'Vercelli', '003': 'Novara', '004': 'Cuneo', '005': 'Asti',
            '006': 'Alessandria', '007': 'Valle d\'Aosta/Vallée d\'Aoste', '008': 'Imperia', '009': 'Savona',
            '010': 'Genova', '011': 'La Spezia', '012': 'Varese', '013': 'Como', '014': 'Sondrio',
            '015': 'Milano', '016': 'Bergamo', '017': 'Brescia', '018': 'Pavia', '019': 'Cremona',
            '020': 'Mantova', '021': 'Bolzano/Bozen', '022': 'Trento', '023': 'Verona', '024': 'Vicenza',
            '025': 'Belluno', '026': 'Treviso', '027': 'Venezia', '028': 'Padova', '029': 'Rovigo',
            '030': 'Udine', '031': 'Gorizia', '032': 'Trieste', '033': 'Piacenza', '034': 'Parma',
            '035': 'Reggio nell\'Emilia', '036': 'Modena', '037': 'Bologna', '038': 'Ferrara', '039': 'Ravenna',
            '040': 'Forlì-Cesena', '041': 'Pesaro e Urbino', '042': 'Ancona', '043': 'Macerata', '044': 'Ascoli Piceno',
            '045': 'Massa-Carrara', '046': 'Lucca', '047': 'Pistoia', '048': 'Firenze', '049': 'Livorno',
            '050': 'Pisa', '051': 'Arezzo', '052': 'Siena', '053': 'Grosseto', '054': 'Perugia',
            '055': 'Terni', '056': 'Viterbo', '057': 'Rieti', '058': 'Roma', '059': 'Latina',
            '060': 'Frosinone', '061': 'Caserta', '062': 'Benevento', '063': 'Napoli', '064': 'Avellino',
            '065': 'Salerno', '066': 'L\'Aquila', '067': 'Teramo', '068': 'Pescara', '069': 'Chieti',
            '070': 'Campobasso', '071': 'Foggia', '072': 'Bari', '073': 'Taranto', '074': 'Brindisi',
            '075': 'Lecce', '076': 'Potenza', '077': 'Matera', '078': 'Cosenza', '079': 'Catanzaro',
            '080': 'Reggio Calabria', '081': 'Trapani', '082': 'Palermo', '083': 'Messina', '084': 'Agrigento',
            '085': 'Caltanissetta', '086': 'Enna', '087': 'Catania', '088': 'Ragusa', '089': 'Siracusa',
            '090': 'Sassari', '091': 'Nuoro', '092': 'Cagliari', '093': 'Pordenone', '094': 'Isernia',
            '095': 'Oristano', '096': 'Biella', '097': 'Lecco', '098': 'Lodi', '099': 'Rimini',
            '100': 'Prato', '101': 'Crotone', '102': 'Vibo Valentia', '103': 'Verbano-Cusio-Ossola',
            '108': 'Monza e della Brianza', '109': 'Fermo', '110': 'Barletta-Andria-Trani', '111': 'Sud Sardegna',
            # Supporto per numeri interi (come restituisce GSE)
            1: 'Torino', 2: 'Vercelli', 3: 'Novara', 4: 'Cuneo', 5: 'Asti',
            6: 'Alessandria', 7: 'Valle d\'Aosta/Vallée d\'Aoste', 8: 'Imperia', 9: 'Savona',
            10: 'Genova', 11: 'La Spezia', 12: 'Varese', 13: 'Como', 14: 'Sondrio',
            15: 'Milano', 16: 'Bergamo', 17: 'Brescia', 18: 'Pavia', 19: 'Cremona',
            20: 'Mantova', 21: 'Bolzano/Bozen', 22: 'Trento', 23: 'Verona', 24: 'Vicenza',
            25: 'Belluno', 26: 'Treviso', 27: 'Venezia', 28: 'Padova', 29: 'Rovigo',
            30: 'Udine', 31: 'Gorizia', 32: 'Trieste', 33: 'Piacenza', 34: 'Parma',
            35: 'Reggio nell\'Emilia', 36: 'Modena', 37: 'Bologna', 38: 'Ferrara', 39: 'Ravenna',
            40: 'Forlì-Cesena', 41: 'Pesaro e Urbino', 42: 'Ancona', 43: 'Macerata', 44: 'Ascoli Piceno',
            45: 'Massa-Carrara', 46: 'Lucca', 47: 'Pistoia', 48: 'Firenze', 49: 'Livorno',
            50: 'Pisa', 51: 'Arezzo', 52: 'Siena', 53: 'Grosseto', 54: 'Perugia',
            55: 'Terni', 56: 'Viterbo', 57: 'Rieti', 58: 'Roma', 59: 'Latina',
            60: 'Frosinone', 61: 'Caserta', 62: 'Benevento', 63: 'Napoli', 64: 'Avellino',
            65: 'Salerno', 66: 'L\'Aquila', 67: 'Teramo', 68: 'Pescara', 69: 'Chieti',
            70: 'Campobasso', 71: 'Foggia', 72: 'Bari', 73: 'Taranto', 74: 'Brindisi',
            75: 'Lecce', 76: 'Potenza', 77: 'Matera', 78: 'Cosenza', 79: 'Catanzaro',
            80: 'Reggio Calabria', 81: 'Trapani', 82: 'Palermo', 83: 'Messina', 84: 'Agrigento',
            85: 'Caltanissetta', 86: 'Enna', 87: 'Catania', 88: 'Ragusa', 89: 'Siracusa',
            90: 'Sassari', 91: 'Nuoro', 92: 'Cagliari', 93: 'Pordenone', 94: 'Isernia',
            95: 'Oristano', 96: 'Biella', 97: 'Lecco', 98: 'Lodi', 99: 'Rimini',
            100: 'Prato', 101: 'Crotone', 102: 'Vibo Valentia', 103: 'Verbano-Cusio-Ossola',
            108: 'Monza e della Brianza', 109: 'Fermo', 110: 'Barletta-Andria-Trani', 111: 'Sud Sardegna'
        }
    
    def resolve_pod(self, pod_code: str) -> PODResult:
        """
        Risolve un POD e restituisce tutte le informazioni associate.
        
        Args:
            pod_code (str): Codice POD da risolvere (es: "IT001E12345678")
            
        Returns:
            PODResult: Oggetto contenente tutte le informazioni del POD
            
        Raises:
            ValueError: Se il formato del POD non è valido
            RuntimeError: Se si verifica un errore durante la risoluzione
            
        Example:
            >>> resolver = GSEPodResolver()
            >>> result = resolver.resolve_pod("IT001E12345678")
            >>> print(f"POD: {result.pod}")
            >>> print(f"Cabina Primaria: {result.cabina_primaria}")
            >>> print(f"Fornitore: {result.fornitore}")
            >>> print(f"Regioni: {result.regioni}")
            >>> print(f"Province: {result.province}")
            >>> print(f"Comuni: {result.comuni}")
        """
        # Validazione input
        if not self._validate_pod_format(pod_code):
            raise ValueError(f"Formato POD non valido: {pod_code}. Formato atteso: ITxxxExxxxxxxx")
        
        try:
            logger.info(f"Avvio risoluzione POD: {pod_code}")
            
            # 1. Trova AC per il POD
            ac_info = self._find_ac_for_pod(pod_code)
            if not ac_info:
                raise RuntimeError(f"AC non trovato per il POD: {pod_code}")
            
            logger.info(f"AC trovato: {ac_info['COD_AC']}")
            
            # 2. Ottieni informazioni geografiche dall'AC
            geographic_info = self._get_geographic_info_from_ac(ac_info['COD_AC'])
            
            # 3. Crea e restituisci il risultato
            result = PODResult(
                pod=pod_code,
                cabina_primaria=ac_info['COD_AC'],
                fornitore=geographic_info['fornitore'],
                regioni=geographic_info['regioni'],
                province=geographic_info['province'],
                comuni=geographic_info['comuni']
            )
            
            logger.info(f"POD {pod_code} risolto con successo")
            return result
            
        except Exception as e:
            logger.error(f"Errore nella risoluzione del POD {pod_code}: {str(e)}")
            raise RuntimeError(f"Errore nella risoluzione del POD: {str(e)}")
    
    def _validate_pod_format(self, pod_code: str) -> bool:
        """
        Valida il formato del codice POD.
        
        Args:
            pod_code (str): Codice POD da validare
            
        Returns:
            bool: True se il formato è valido, False altrimenti
        """
        import re
        pattern = r'^IT\d{3}E\d{8}$'
        return bool(re.match(pattern, pod_code))
    
    def _find_ac_for_pod(self, pod_code: str) -> Optional[Dict]:
        """
        Trova la cabina primaria (AC) associata a un POD.
        
        Args:
            pod_code (str): Codice POD
            
        Returns:
            Optional[Dict]: Dizionario con COD_POD e COD_AC, None se non trovato
        """
        url = f"{self.base_url}/TIAD2/POD_AC/FeatureServer/12/query"
        params = {
            'where': f"COD_POD='{pod_code}'",
            'outFields': 'COD_POD,COD_AC',
            'f': 'json'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                return data['features'][0]['attributes']
            return None
            
        except requests.RequestException as e:
            logger.error(f"Errore nella richiesta per trovare AC: {str(e)}")
            raise RuntimeError(f"Errore di connessione: {str(e)}")
    
    def _get_geographic_info_from_ac(self, ac_code: str) -> Dict:
        """
        Ottiene informazioni geografiche da una cabina primaria.
        
        Args:
            ac_code (str): Codice della cabina primaria
            
        Returns:
            Dict: Dizionario con fornitore, regioni, province e comuni
        """
        try:
            # 1. Ottieni geometria AC e fornitore
            ac_info = self._get_ac_info(ac_code)
            if not ac_info:
                raise RuntimeError(f"Informazioni AC non trovate: {ac_code}")
            
            # 2. Trova comuni che intersecano l'AC
            comuni = self._find_comuni_intersecting_ac(ac_info['geometry'])
            
            if not comuni or len(comuni) == 0:
                raise RuntimeError(f"Nessun comune trovato per l'AC: {ac_code}")
            
            # 3. Estrai tutte le regioni e province uniche dai comuni
            regioni_uniche = list(set(comune['COD_REG'] for comune in comuni))
            province_uniche = list(set(comune['COD_PROV'] for comune in comuni))
            
            # 4. Traduci in nomi completi
            nomi_regioni = [self._get_regione_name(cod) for cod in regioni_uniche]
            nomi_province = [self._get_provincia_name(cod) for cod in province_uniche]
            
            return {
                'fornitore': ac_info['fornitore'],
                'regioni': ', '.join(nomi_regioni),
                'province': ', '.join(nomi_province),
                'comuni': ', '.join(comune['COMUNE'] for comune in comuni)
            }
            
        except Exception as e:
            logger.error(f"Errore nell'ottenimento info geografiche per AC {ac_code}: {str(e)}")
            raise
    
    def _get_ac_info(self, ac_code: str) -> Optional[Dict]:
        """
        Ottiene informazioni dettagliate di una cabina primaria.
        
        Args:
            ac_code (str): Codice della cabina primaria
            
        Returns:
            Optional[Dict]: Dizionario con geometria e fornitore, None se non trovato
        """
        url = f"{self.base_url}/TIAD2/Aree_Convenzionali/FeatureServer/0/query"
        params = {
            'where': f"COD_AC='{ac_code}'",
            'outFields': 'COD_AC,RAG_SOC',
            'returnGeometry': 'true',
            'f': 'json'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                

                
                return {
                    'geometry': feature['geometry'],
                    'fornitore': feature['attributes'].get('RAG_SOC', 'Non specificato')
                }
            return None
            
        except requests.RequestException as e:
            logger.error(f"Errore nella richiesta per AC {ac_code}: {str(e)}")
            raise RuntimeError(f"Errore di connessione: {str(e)}")
    
    def _find_comuni_intersecting_ac(self, ac_geometry: Dict) -> List[Dict]:
        """
        Trova i comuni che intersecano una cabina primaria.
        
        Args:
            ac_geometry (Dict): Geometria della cabina primaria
            
        Returns:
            List[Dict]: Lista di comuni con attributi COMUNE, COD_REG, COD_PROV
        """
        url = f"{self.base_url}/TIAD2/Comuni/FeatureServer/10/query"
        
        # Crea una geometria semplificata per la query spaziale
        # Gestisce il caso in cui spatialReference potrebbe non essere presente
        simplified_geometry = {
            'rings': ac_geometry.get('rings', []),
            'spatialReference': ac_geometry.get('spatialReference', {'wkid': 4326})
        }
        
        # Verifica che la geometria sia valida
        if not simplified_geometry['rings']:
            logger.warning("Geometria AC senza rings, impossibile eseguire query spaziale")
            return []
        
        spatial_query = {
            'geometry': json.dumps(simplified_geometry),
            'geometryType': 'esriGeometryPolygon',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'COMUNE,COD_REG,COD_PROV',
            'f': 'json'
        }
        
        try:
            response = self.session.post(url, data=spatial_query)
            response.raise_for_status()
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                return [feature['attributes'] for feature in data['features']]
            return []
            
        except requests.RequestException as e:
            logger.error(f"Errore nella query spaziale: {str(e)}")
            raise RuntimeError(f"Errore di connessione: {str(e)}")
    
    def _get_regione_name(self, cod_reg: Union[str, int]) -> str:
        """
        Traduce un codice regione in nome leggibile.
        
        Args:
            cod_reg (Union[str, int]): Codice regione
            
        Returns:
            str: Nome della regione o "Regione {codice}" se non trovato
        """
        return self.regioni_map.get(cod_reg, f"Regione {cod_reg}")
    
    def _get_provincia_name(self, cod_prov: Union[str, int]) -> str:
        """
        Traduce un codice provincia in nome leggibile.
        
        Args:
            cod_prov (Union[str, int]): Codice provincia
            
        Returns:
            str: Nome della provincia o "Provincia {codice}" se non trovato
        """
        return self.province_map.get(cod_prov, f"Provincia {cod_prov}")
    
    def close(self):
        """Chiude la sessione HTTP."""
        self.session.close()
        logger.info("Sessione HTTP chiusa")
    
    def __enter__(self):
        """Supporto per context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Supporto per context manager."""
        self.close()


def main():
    """
    Funzione principale per test e utilizzo da riga di comando.
    
    Usage:
        python gse_pod_resolver.py IT001E12345678
    """
    import sys
    
    if len(sys.argv) != 2:
        print("🔌 GSE POD Resolver - Test")
        print("=" * 50)
        print("Usage: python gse_pod_resolver.py <CODICE_POD>")
        print("Esempio: python gse_pod_resolver.py IT001E12345678")
        sys.exit(1)
    
    pod_code = sys.argv[1]
    print("🔌 GSE POD Resolver - Test")
    print("=" * 50)
    
    try:
        with GSEPodResolver() as resolver:
            print(f"\n🔍 Test POD: {pod_code}")
            print("-" * 30)
            
            result = resolver.resolve_pod(pod_code)
            print(f"✅ POD: {result.pod}")
            print(f"✅ Cabina Primaria: {result.cabina_primaria}")
            print(f"✅ Fornitore: {result.fornitore}")
            print(f"✅ Regioni: {result.regioni}")
            print(f"✅ Province: {result.province}")
            print(f"✅ Comuni: {result.comuni}")
            
            print("-" * 30)
    
    except Exception as e:
        print(f"❌ Errore: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
