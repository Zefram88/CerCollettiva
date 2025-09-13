# documents/processors/gaudi.py
import logging
import re
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from django.utils.translation import gettext as _

import PyPDF2

logger = logging.getLogger(__name__)


class GaudiProcessor:
    """Processore per l'attestazione Gaudì"""

    def __init__(self, document):
        self.document = document
        self.content = None
        self.data = {}

    def process(self):
        """
        Processa l'attestazione Gaudì estraendo e validando tutti i dati necessari.
        """
        try:
            # Leggi il contenuto del file PDF
            file_content = self.document.file.read()
            pdf_file = BytesIO(file_content)

            try:
                # Estrai il testo dal PDF
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())

                self.content = "\n".join(text_content)
                logger.debug("Contenuto PDF estratto con successo")
                logger.debug(f"Lunghezza contenuto: {len(self.content)} caratteri")

            except Exception as e:
                logger.error(f"Errore nell'estrazione del testo dal PDF: {str(e)}")
                raise ValueError(_("Impossibile leggere il contenuto del PDF"))

            # Verifica il POD
            pod = self._extract_pod()
            logger.debug(f"POD estratto dall'attestato: {pod}")

            # Rimuoviamo il controllo rigido del POD qui
            # Il controllo viene fatto nella view, che gestisce la conferma dell'utente

            # Estrai i dati
            self._extract_data()

            # Aggiorna il documento
            from django.utils import timezone

            self.document.processing_status = "COMPLETED"
            self.document.processed_at = timezone.now()
            self.document.save()

            logger.info(
                f"Attestato Gaudì elaborato con successo per impianto "
                f"{self.document.plant.pod_code}"
            )
            return self.data

        except Exception as e:
            error_msg = f"Errore nell'elaborazione dell'attestato: {str(e)}"
            logger.error(error_msg)
            self._handle_processing_error(error_msg)
            raise

    def _extract_pod(self) -> str:
        """
        Estrae il codice POD dal documento usando vari pattern di ricerca.
        """
        logger.debug("Cercando il POD nel contenuto del documento")

        # Simple line-by-line search first
        lines = self.content.split("\n")

        for i, line in enumerate(lines):
            # If this line contains 'Codice POD:', look at the next line
            if "Codice POD:" in line:
                logger.debug(f"Trovata linea con 'Codice POD:': {line}")

                # Look in current line
                pod_match = re.search(r"IT001E\d{9}", line)
                if pod_match:
                    pod = pod_match.group(0)
                    logger.debug(f"POD trovato nella stessa linea: {pod}")
                    return pod

                # Check next line if exists
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    logger.debug(f"Controllando la linea successiva: {next_line}")
                    if next_line.startswith("IT001E"):
                        pod = next_line.split()[0]
                        logger.debug(f"POD trovato nella linea successiva: {pod}")
                        return pod

        # Try to find any POD pattern in the whole text
        text = " ".join(lines)
        matches = re.findall(r"IT001E\d{9}", text)
        if matches:
            pod = matches[0]
            logger.debug(f"POD trovato nel testo completo: {pod}")
            return pod

        logger.error("Nessun POD trovato nel documento")
        raise ValueError(_("POD non trovato nell'attestato"))

    def _handle_processing_error(self, error_msg: str):
        """Gestisce gli errori di elaborazione in modo centralizzato"""
        from django.utils import timezone

        self.document.processing_status = "FAILED"
        self.document.processing_errors = error_msg
        self.document.processed_at = timezone.now()  # Usa timezone-aware datetime
        self.document.save()

    def _parse_date(self, date_str: str, format: str = "%d/%m/%Y %H:%M:%S") -> datetime:
        """
        Converte una stringa in data senza ora.
        Pulisce prima la stringa da eventuali caratteri extra.
        """
        try:
            # Pulisci la stringa della data e prendi solo la parte della data
            date_str = date_str.strip().split()[0] if " " in date_str else date_str

            # Formati possibili per il parsing
            formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]

            # Prima prova il formato specificato
            try:
                return datetime.strptime(date_str, format).date()
            except ValueError:
                # Se fallisce, prova gli altri formati
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue

            raise ValueError(_(f"Formato data non valido: {date_str}"))

        except Exception as e:
            logger.error(f"Impossibile parsare la data: {date_str} - {e}")
            raise ValueError(_(f"Formato data non valido: {date_str}"))

    def _parse_int(self, value_str: str) -> int:
        """
        Converte una stringa in intero, gestendo anche valori con decimali.
        """
        try:
            # Rimuovi eventuali spazi e sostituisci la virgola con il punto
            clean_value = value_str.strip().replace(",", ".")
            # Rimuovi eventuali unità di misura
            clean_value = re.sub(r"\s*[a-zA-Z]+\s*$", "", clean_value)
            # Se è un numero decimale, converti prima in float e poi in int
            return int(float(clean_value))
        except (ValueError, TypeError) as e:
            logger.error(
                f"Errore nella conversione del valore {value_str} in intero: {str(e)}"
            )
            raise ValueError(f"Valore numerico non valido: {value_str}")

    def _update_plant(self):
        """Aggiorna l'impianto con i dati estratti"""
        plant = self.document.plant
        for key, value in self.data.items():
            setattr(plant, key, value)
        plant.gaudi_verified = True
        plant.save()

    def _extract_value(self, field_name: str, required: bool = True) -> str:
        """
        Estrae un valore specifico dal documento, gestendo vari formati di campi.
        """
        try:
            logger.debug(f"Cercando campo: {field_name}")
            lines = self.content.split("\n")

            # Dictionary di campi alternativi
            field_alternatives = {
                "Potenza Apparente Nominale": [
                    "Potenza Apparente Nominale",
                    "Potenza Apparente Nominale (kVA)",
                    "Potenza Apparente Nominale (kVA):",
                ],
                "Tensione generatore": [
                    "Tensione generatore",
                    "Tensione generatore (V)",
                    "Tensione generatore (V):",
                ],
                "Produzione Lorda Media Annua": [
                    "Produzione Lorda Media Annua",
                    "Produzione Lorda Media Annua (kWh)",
                    "Produzione Lorda Media Annua (kWh):",
                ],
            }

            # Ottieni le varianti del nome del campo
            field_names = field_alternatives.get(field_name, [field_name])

            # Cerca tutte le varianti del nome del campo
            for fname in field_names:
                for i, line in enumerate(lines):
                    if fname in line:
                        value = line.split(":", 1)[1].strip() if ":" in line else ""

                        # Se la linea è vuota, prendi il valore dalla linea successiva
                        if not value and i + 1 < len(lines):
                            value = lines[i + 1].strip()

                        # Rimuovi eventuali linee extra dopo il valore
                        value = value.split("\n")[0].strip()

                        if value:  # Se abbiamo trovato un valore
                            logger.debug(f"Trovato valore per {field_name}: {value}")
                            return value

            if required:
                raise ValueError(_(f"Campo {field_name} non trovato nell'attestato"))
            return ""  # Ritorna stringa vuota per campi non richiesti

        except Exception as e:
            if required:
                logger.error(f"Errore nell'estrazione del campo {field_name}: {str(e)}")
                # logger.debug("Contenuto del documento:")
                # logger.debug(self.content)
                raise ValueError(
                    _(f"Errore nell'estrazione del campo {field_name}: {str(e)}")
                )
        return ""

    def _parse_float(self, value_str: str) -> float:
        """
        Converte una stringa in float, gestendo formati italiani con virgola.
        """
        try:
            # Rimuovi eventuali spazi e sostituisci la virgola con il punto
            clean_value = value_str.strip().replace(",", ".")
            # Rimuovi eventuali unità di misura
            clean_value = re.sub(r"\s*[a-zA-Z]+\s*$", "", clean_value)
            return float(clean_value)
        except (ValueError, TypeError) as e:
            logger.error(
                f"Errore nella conversione del valore {value_str} in float: {str(e)}"
            )
            raise ValueError(f"Valore numerico non valido: {value_str}")

    def _extract_cap(self, address: str) -> str:
        """Estrae il CAP dall'indirizzo"""
        cap_match = re.search(r"\b\d{5}\b", address)
        return cap_match.group(0) if cap_match else None

    def _extract_data(self):
        try:
            # Estrai valori grezzi con validazione
            validation_date_str = self._extract_value(
                "Data di Convalida", required=True
            )
            expected_operation_date_str = self._extract_value(
                "Data presunto esercizio", required=False
            )

            # Se la data di presunto esercizio è vuota, usa la data di convalida
            if not expected_operation_date_str:
                logger.info(
                    "Data presunto esercizio non trovata, usando data di "
                    "convalida come fallback"
                )
                expected_operation_date_str = validation_date_str
                self.data["using_validation_date_as_fallback"] = True
            else:
                self.data["using_validation_date_as_fallback"] = False

            nominal_power_str = self._extract_value("Potenza Apparente Nominale")
            voltage_str = self._extract_value("Tensione generatore")
            voltage = self._parse_int(voltage_str)
            production_str = self._extract_value("Produzione Lorda Media Annua")
            address = self._extract_value("Ubicazione Impianto")
            cap = self._extract_cap(address)

            self.data = {
                # Dati di base
                "gaudi_request_code": self._extract_value("Codice Richiesta"),
                "censimp_code": self._extract_value("Codice CENSIMP"),
                "validation_date": self._parse_date(validation_date_str),
                "nominal_power": self._parse_float(nominal_power_str),
                "connection_voltage": voltage,  # Usa tensione generatore
                "voltage": voltage,
                "expected_yearly_production": self._parse_int(production_str),
                "installation_date": self._parse_date(
                    expected_operation_date_str, "%d/%m/%Y"
                ),  # Data presunto esercizio
                "expected_operation_date": self._parse_date(
                    expected_operation_date_str, "%d/%m/%Y"
                ),
                # Info impianto
                "plant_name": self._extract_value("Nome Impianto"),
                "plant_type": self._extract_value("Tipologia Impianto"),
                "tracking_code": self._extract_value("Codice di rintracciabilità"),
                "sapr_code": self._extract_value("Codice SAPR"),
                "address": address,
                "cap": cap,
                "grid_operator": self._extract_value("Gestore della rete elettrica"),
                "version_number": self._parse_int(
                    self._extract_value("Numero versione attestato")
                ),
                "has_storage": False,
                # Info produttore
                "producer_name": self._extract_value("Rag. Sociale"),
                "producer_vat": self._extract_value("P.IVA \\ Cod. Fisc."),
                "producer_address": self._extract_value("Indirizzo"),
                # Dati tecnici
                "generator_group_id": self._extract_value("Gruppo N°").split(" - ")[0],
                "section_type": "SILICIO MONOCRISTALLINO",
                "section_id": self._extract_value("Identificativo Sezione CENSIMP"),
                "group_id": self._extract_value("Identificativo Gruppo CENSIMP"),
                "remote_disconnect": self._extract_value("Predisposizione Teledistacco")
                == "SI",
                "active_power": self._parse_float(
                    self._extract_value(
                        "Potenza Attiva Nominale del Generatore"
                    ).split()[0]
                ),
                "net_power": self._parse_float(
                    self._extract_value("Potenza Efficiente Netta").split()[0]
                ),
                "gross_power": self._parse_float(
                    self._extract_value("Potenza Efficiente Lorda").split()[0]
                ),
                "grid_feed_type": (
                    "TOTAL"
                    if self._extract_value(
                        "Produzione immessa su rete elettrica"
                    ).lower()
                    == "si tutta"
                    else "PARTIAL"
                ),
            }

            # Log per debug
            for key, value in self.data.items():
                logger.debug(f"{key}: {value}")

        except Exception as e:
            logger.error(f"Errore nell'estrazione dei dati: {str(e)}")
            raise ValueError(f"Errore nell'estrazione dei dati: {str(e)}")

    def extract_data_only(self) -> Dict[str, Any]:
        """
        Estrae i dati dall'attestato Gaudì senza validazioni sull'impianto.
        Usato per precompilare il form di creazione impianto.
        """
        try:
            # Leggi il contenuto del file PDF
            file_content = self.document.file.read()
            pdf_file = BytesIO(file_content)

            try:
                # Estrai il testo dal PDF
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())

                self.content = "\n".join(text_content)
                logger.debug("Contenuto PDF estratto con successo")
                logger.debug(f"Lunghezza contenuto: {len(self.content)} caratteri")

            except Exception as e:
                logger.error(f"Errore nell'estrazione del testo dal PDF: {str(e)}")
                raise ValueError(_("Impossibile leggere il contenuto del PDF"))

            # Estrai il POD senza verifiche sull'impianto
            pod = self._extract_pod()

            # Estrai tutti i dati
            self._extract_data()

            # Aggiungi il POD ai dati estratti
            self.data["pod_code"] = pod

            return self.data

        except Exception as e:
            error_msg = f"Errore nell'elaborazione dell'attestato: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def preview_gaudi_changes(self, plant) -> Dict[str, Dict[str, Any]]:
        """
        Confronta i dati estratti con i dati esistenti dell'impianto
        e restituisce un dizionario delle modifiche proposte.
        """
        changes = {}

        # Mappa dei campi da confrontare con le relative etichette
        field_mappings = {
            "installation_date": ("validation_date", "Data Installazione"),
            "address": ("address", "Indirizzo"),
            "connection_voltage": ("voltage", "Tensione Connessione"),
            "nominal_power": ("nominal_power", "Potenza Nominale"),
            "expected_yearly_production": (
                "expected_yearly_production",
                "Produzione Annua Attesa",
            ),
            "gaudi_request_code": ("gaudi_request_code", "Codice Richiesta Gaudì"),
            "censimp_code": ("censimp_code", "Codice CENSIMP"),
            "active_power": ("active_power", "Potenza Attiva"),
            "net_power": ("net_power", "Potenza Netta"),
            "gross_power": ("gross_power", "Potenza Lorda"),
        }

        # Estrai i dati Gaudì senza salvare
        gaudi_data = self.extract_data_only()

        # Confronta i campi
        for plant_field, (gaudi_field, label) in field_mappings.items():
            old_value = getattr(plant, plant_field, None)
            new_value = gaudi_data.get(gaudi_field)

            if old_value != new_value and new_value is not None:
                changes[plant_field] = {
                    "old": old_value,
                    "new": new_value,
                    "label": label,
                }

        return changes

    def is_using_validation_date_fallback(self) -> bool:
        """
        Verifica se stiamo usando la data di convalida come fallback per la
        data di presunto esercizio.
        """
        return self.data.get("using_validation_date_as_fallback", False)

    def get_date_fallback_message(self) -> Optional[str]:
        """
        Restituisce un messaggio informativo se stiamo usando la data di
        convalida come fallback.
        """
        if self.is_using_validation_date_fallback():
            validation_date = self.data.get("validation_date")
            if validation_date:
                return _(
                    f"La data di presunto esercizio non era specificata. "
                    f"È stata utilizzata la data di convalida "
                    f"({validation_date.strftime('%d/%m/%Y')}) "
                    f"come data di presunto esercizio."
                )
        return None
