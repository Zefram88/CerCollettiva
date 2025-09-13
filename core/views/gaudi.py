# core/views/gaudi.py
# import pytz
import logging
import re
from datetime import date, datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from documents.models import Document
from documents.processors.gaudi import GaudiProcessor

from ..forms import InitialGaudiUploadForm, PlantForm, PlantGaudiUpdateForm
from ..models import Plant
from .base import BasePlantView

logger = logging.getLogger(__name__)


def setup_logging():
    """Configurazione avanzata del logging"""
    logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=logging_format)


class GaudiAddressMixin:
    """Mixin per la gestione degli indirizzi negli attestati Gaudì"""

    def _get_province_code(self, province: str) -> str:
        """
        Converte il nome della provincia nel suo codice di due lettere.
        Gestisce sia nomi completi che codici esistenti.
        """
        # Dizionario delle province italiane (mantenere il dizionario esistente)
        PROVINCE_MAPPING = {
            # Nord
            "TORINO": "TO",
            "VERCELLI": "VC",
            "NOVARA": "NO",
            "CUNEO": "CN",
            "ASTI": "AT",
            "ALESSANDRIA": "AL",
            "AOSTA": "AO",
            "IMPERIA": "IM",
            "SAVONA": "SV",
            "GENOVA": "GE",
            "LA SPEZIA": "SP",
            "VARESE": "VA",
            "COMO": "CO",
            "SONDRIO": "SO",
            "MILANO": "MI",
            "BERGAMO": "BG",
            "BRESCIA": "BS",
            "PAVIA": "PV",
            "CREMONA": "CR",
            "MANTOVA": "MN",
            "BOLZANO": "BZ",
            "TRENTO": "TN",
            "VERONA": "VR",
            "VICENZA": "VI",
            "BELLUNO": "BL",
            "TREVISO": "TV",
            "VENEZIA": "VE",
            "PADOVA": "PD",
            "ROVIGO": "RO",
            "UDINE": "UD",
            "GORIZIA": "GO",
            "TRIESTE": "TS",
            "PIACENZA": "PC",
            "PARMA": "PR",
            "REGGIO EMILIA": "RE",
            "MODENA": "MO",
            "BOLOGNA": "BO",
            "FERRARA": "FE",
            "RAVENNA": "RA",
            "FORLI-CESENA": "FC",
            "RIMINI": "RN",
            "MASSA-CARRARA": "MS",
            "LUCCA": "LU",
            "PISTOIA": "PT",
            "FIRENZE": "FI",
            "LIVORNO": "LI",
            "PISA": "PI",
            "AREZZO": "AR",
            "SIENA": "SI",
            "GROSSETO": "GR",
            # Centro
            "PERUGIA": "PG",
            "TERNI": "TR",
            "PESARO E URBINO": "PU",
            "ANCONA": "AN",
            "MACERATA": "MC",
            "ASCOLI PICENO": "AP",
            "VITERBO": "VT",
            "RIETI": "RI",
            "ROMA": "RM",
            "LATINA": "LT",
            "FROSINONE": "FR",
            # Sud e Isole
            "L'AQUILA": "AQ",
            "TERAMO": "TE",
            "PESCARA": "PE",
            "CHIETI": "CH",
            "CAMPOBASSO": "CB",
            "ISERNIA": "IS",
            "CASERTA": "CE",
            "BENEVENTO": "BN",
            "NAPOLI": "NA",
            "AVELLINO": "AV",
            "SALERNO": "SA",
            "FOGGIA": "FG",
            "BARI": "BA",
            "TARANTO": "TA",
            "BRINDISI": "BR",
            "LECCE": "LE",
            "POTENZA": "PZ",
            "MATERA": "MT",
            "COSENZA": "CS",
            "CATANZARO": "CZ",
            "REGGIO CALABRIA": "RC",
            "TRAPANI": "TP",
            "PALERMO": "PA",
            "MESSINA": "ME",
            "AGRIGENTO": "AG",
            "CALTANISSETTA": "CL",
            "ENNA": "EN",
            "CATANIA": "CT",
            "RAGUSA": "RG",
            "SIRACUSA": "SR",
            "SASSARI": "SS",
            "NUORO": "NU",
            "CAGLIARI": "CA",
            "PORDENONE": "PN",
            "ISERNIA": "IS",
            "ORISTANO": "OR",
            # Province di nuova istituzione
            "MONZA E BRIANZA": "MB",
            "FERMO": "FM",
            "BARLETTA-ANDRIA-TRANI": "BT",
            "SUD SARDEGNA": "SU",
            "VERBANO-CUSIO-OSSOLA": "VB",
            "BIELLA": "BI",
            "LECCO": "LC",
            "LODI": "LO",
            "RIMINI": "RN",
            "PRATO": "PO",
            "CROTONE": "KR",
            "VIBO VALENTIA": "VV",
        }

        if not province:
            logger.warning("Provincia non specificata")
            return ""

        province = province.strip().upper()

        if len(province) == 2 and province.isalpha():
            return province

        if province in PROVINCE_MAPPING:
            return PROVINCE_MAPPING[province]

        special_cases = {
            "ROMA CAPITALE": "RM",
            "CITTA METROPOLITANA DI ROMA": "RM",
            "MILANO CITTA METROPOLITANA": "MI",
            "NAPOLI CITTA METROPOLITANA": "NA",
        }
        if province in special_cases:
            return special_cases[province]

        logger.warning(f"Provincia non trovata nel mapping: {province}")

        if len(province) >= 2 and province[:2].isalpha():
            logger.info(
                f"Usando le prime due lettere come codice provincia per: {province}"
            )
            return province[:2]

        return province

    def _parse_address(self, full_address: str) -> dict:
        """
        Analizza e normalizza l'indirizzo dall'attestato Gaudì.
        """
        result = {"address": "", "city": "", "province": "", "zip_code": ""}

        if not full_address:
            return result

        try:
            logger.debug(f"Parsing indirizzo: {full_address}")

            clean_address = (
                full_address.replace("Italia", "")
                .replace("  ", " ")
                .replace(" ,", ",")
                .replace(", ,", ",")
                .strip()
            )

            # Rimuove parole duplicate consecutive
            words = clean_address.split()
            clean_words = []
            prev_word = None
            for word in words:
                if word != prev_word:
                    clean_words.append(word)
                prev_word = word
            clean_address = " ".join(clean_words)

            # Estrazione CAP
            cap_match = re.search(r"(\d{5})", clean_address)
            if cap_match:
                result["zip_code"] = cap_match.group(1)
                clean_address = clean_address.replace(result["zip_code"], "")
                logger.debug(f"CAP trovato: {result['zip_code']}")

            # Estrazione Provincia
            prov_match = re.search(r"\(([^)]+)\)", clean_address)
            if prov_match:
                provincia = prov_match.group(1).strip()
                result["province"] = self._get_province_code(provincia)
                clean_address = clean_address.replace(f"({provincia})", "").strip()

            city_parts = [part.strip() for part in clean_address.split(",")]
            if len(city_parts) > 1:
                city_part = (
                    city_parts[-2].strip()
                    if len(city_parts) > 2
                    else city_parts[-1].strip()
                )
                city_part = re.sub(r"\d+", "", city_part).strip()
                if "MIRA" in city_part.upper():
                    result["city"] = "Mira"
                else:
                    result["city"] = " ".join(
                        word.capitalize() for word in city_part.split()
                    )

                address_parts = (
                    city_parts[:-2] if len(city_parts) > 2 else [city_parts[0]]
                )
                result["address"] = ", ".join(part.strip() for part in address_parts)
            else:
                result["address"] = clean_address

            if result["address"]:
                result["address"] = (
                    result["address"].replace(result["city"], "").strip(" ,")
                )
                result["address"] = " ".join(
                    word.capitalize() for word in result["address"].split()
                )

            logger.debug(f"Indirizzo originale: {full_address}")
            logger.debug(f"Indirizzo normalizzato: {result}")

            return result

        except Exception as e:
            logger.error(
                f"Errore nel parsing dell'indirizzo '{full_address}': {str(e)}"
            )
            return result


@method_decorator(require_http_methods(["GET", "POST"]), name="dispatch")
class NewPlantFromGaudiView(GaudiAddressMixin, BasePlantView, FormView):
    """Creazione di un nuovo impianto da attestato Gaudì"""

    template_name = "core/plant_from_gaudi.html"
    form_class = InitialGaudiUploadForm
    success_url = reverse_lazy("core:plant_list")

    def form_valid(self, form):  # Gestisce il caricamento iniziale del file Gaudì
        try:
            # Crea documento temporaneo
            temp_doc = Document.objects.create(
                type="GAUDI_TEMP",
                file=form.cleaned_data["gaudi_file"],
                uploaded_by=self.request.user,
                source="USER",
            )

            try:
                # Processa il documento
                processor = GaudiProcessor(temp_doc)
                gaudi_data = processor.extract_data_only()

                # Parse dell'indirizzo
                parsed_address = self._parse_address(gaudi_data.get("address", ""))
                gaudi_data["parsed_address"] = parsed_address
                gaudi_data["raw_address"] = gaudi_data.get("address", "").strip()

                # Verifica POD duplicato
                pod_code = gaudi_data.get("pod_code")
                if pod_code and Plant.objects.filter(pod_code=pod_code).exists():
                    temp_doc.delete()
                    messages.error(
                        self.request, _(f"Esiste già un impianto con il POD {pod_code}")
                    )
                    return self.form_invalid(form)

                # Salva il riferimento al documento temporaneo
                self.request.session["temp_gaudi_doc"] = temp_doc.id

                # Gestione date
                date_fields = [
                    "validation_date",
                    "installation_date",
                    "expected_operation_date",
                    "commissioning_date",
                ]
                for date_field in date_fields:
                    if gaudi_data.get(date_field):
                        if isinstance(gaudi_data[date_field], (date, datetime)):
                            gaudi_data[date_field] = gaudi_data[date_field].isoformat()

                # Salva i dati in sessione
                self.request.session["plant_gaudi_data"] = gaudi_data

                messages.success(
                    self.request,
                    _(
                        "Attestato elaborato con successo. Seleziona la "
                        "tipologia dell'impianto."
                    ),
                )

                return redirect("core:plant_create_with_gaudi")

            except Exception as process_error:
                temp_doc.delete()
                raise process_error

        except Exception as e:
            logger.error(
                f"Errore durante l'elaborazione dell'attestato Gaudì: {str(e)}"
            )
            messages.error(
                self.request, _("Errore durante l'elaborazione dell'attestato Gaudì")
            )
            return self.form_invalid(form)


class PlantGaudiUpdateView(GaudiAddressMixin, BasePlantView):
    """Aggiornamento dati impianto da attestato Gaudì"""

    template_name = "core/plant_gaudi_update.html"
    form_class = PlantGaudiUpdateForm

    def get_object(self):
        return get_object_or_404(Plant, pk=self.kwargs["pk"], owner=self.request.user)

    def form_valid(
        self, form
    ):  # Gestisce l'aggiornamento di un impianto esistente con dati Gaudì
        try:
            # Crea documento temporaneo
            temp_doc = Document.objects.create(
                type="GAUDI",
                file=form.cleaned_data["gaudi_file"],
                uploaded_by=self.request.user,
                source="USER",
            )

            # Processa il documento
            processor = GaudiProcessor(temp_doc)
            gaudi_data = processor.extract_data_only()

            logger.info("Dati estratti da Gaudì:", gaudi_data)

            # Verifica POD duplicato
            pod_code = gaudi_data.get("pod_code")
            if pod_code and Plant.objects.filter(pod_code=pod_code).exists():
                messages.error(
                    self.request, f"Esiste già un impianto con il POD {pod_code}"
                )
                return self.form_invalid(form)

            # Salva i dati in sessione
            self.request.session["plant_gaudi_data"] = gaudi_data
            logger.info(
                "Dati salvati in sessione:", self.request.session["plant_gaudi_data"]
            )

            messages.success(self.request, "Attestato elaborato con successo")
            return redirect("core:plant_create_with_gaudi")

        except Exception as e:
            logger.error("Errore in NewPlantFromGaudiView:", str(e))
            messages.error(self.request, str(e))
            return self.form_invalid(form)


class PlantCreateFromGaudiView(GaudiAddressMixin, BasePlantView, FormView):
    """Vista per la creazione di un impianto partendo dai dati Gaudì"""

    template_name = "core/plant_from_gaudi.html"
    form_class = PlantForm
    success_url = reverse_lazy("core:plant_list")

    def _process_gaudi_ids(self, gaudi_data):
        """Processa gli ID Gaudì in modo sicuro"""
        results = {"section_id": "", "group_id": ""}

        # Estrai gli ID dalla stringa completa
        section_id = gaudi_data.get("section_id", "")
        group_id = gaudi_data.get("group_id", "")

        # Estrai solo l'ID numerico per section_id
        section_id = gaudi_data.get("section_id", "")
        group_id = gaudi_data.get("group_id", "")

        # Estrai solo l'ID numerico per group_id
        section_match = re.search(r"SZ_(\d+)_\d+", section_id) if section_id else None
        if section_match:
            results["section_id"] = section_match.group(1)[:50]

        # Estrai solo l'ID numerico per group_id
        group_match = re.search(r"GR_(\d+)_\d+_\d+", group_id) if group_id else None
        if group_match:
            results["group_id"] = group_match.group(1)[:50]

        return results

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["from_gaudi"] = True
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        """Verifica la presenza dei dati Gaudì in sessione"""
        logger.debug("Session data: %s", request.session.get("plant_gaudi_data"))

        if "plant_gaudi_data" not in request.session:
            messages.error(request, "Nessun dato Gaudì trovato")
            return redirect("core:plant_new_from_gaudi")
        return super().dispatch(request, *args, **kwargs)

    def _log_field_length(self, model, field_name, value):
        """Logga la lunghezza del campo e il suo valore"""
        if value is None:
            return

        try:
            field = model._meta.get_field(field_name)
            if hasattr(field, "max_length") and isinstance(value, str):
                current_length = len(value)
                max_length = field.max_length
                if current_length > max_length:
                    logger.warning(
                        f"""
                            - Valore: {value}
                            - Lunghezza attuale: {current_length}
                            - Lunghezza massima: {max_length}
                        """
                    )
        except Exception as e:
            logger.error(
                f"Errore nel controllo lunghezza del campo {field_name}: {str(e)}"
            )

    def _convert_date_str(self, date_str):
        """Converte una stringa di data in datetime.date"""
        if not date_str:
            return None

        logger.debug(
            f"[DATE CONVERSION] Input date: {date_str} (type: {type(date_str)})"
        )

        try:
            # Se è già un oggetto date
            if isinstance(date_str, date):
                return date_str

            # Se è un datetime
            if isinstance(date_str, datetime):
                return date_str.date()

            if isinstance(date_str, str):
                # Formato italiano (dd/mm/yyyy)
                if "/" in date_str:
                    logger.debug(
                        "[DATE CONVERSION] Converting Italian format (dd/mm/yyyy)"
                    )
                    day, month, year = map(int, date_str.split("/"))
                    return date(year, month, day)

                # Formato ISO (yyyy-mm-dd)
                if "-" in date_str:
                    logger.debug("[DATE CONVERSION] Converting ISO format (yyyy-mm-dd)")
                    if "T" in date_str:
                        date_str = date_str.split("T")[0]
                    year, month, day = map(int, date_str.split("-"))
                    return date(year, month, day)

            logger.warning(f"[DATE CONVERSION] Format not recognized: {date_str}")
            return None

        except Exception as e:
            logger.error(
                f"[DATE CONVERSION] Error converting date: {date_str} - {str(e)}"
            )
            return None

    def get_initial(self):
        initial = super().get_initial()
        gaudi_data = self.request.session.get("plant_gaudi_data", {})

        parsed_address = gaudi_data.get("parsed_address", {})

        try:
            # Conversione delle date
            # Utilizziamo una funzione dedicata per gestire i vari formati possibili
            dates = {
                "installation_date": self._convert_date_str(
                    gaudi_data.get("installation_date")
                ),
                "validation_date": self._convert_date_str(
                    gaudi_data.get("validation_date")
                ),
                "expected_operation_date": self._convert_date_str(
                    gaudi_data.get("expected_operation_date")
                ),
            }

            # Elaborazione dell'indirizzo utilizzando la funzione dedicata
            # address_components = self._parse_address(
            #     gaudi_data.get("address", "")
            # )  # Unused variable

            # Gestione della tensione di connessione
            connection_voltage = None
            if raw_voltage := gaudi_data.get("connection_voltage"):
                try:
                    # Rimuove 'V' e converte in intero
                    voltage_str = raw_voltage.replace("V", "").strip()
                    connection_voltage = int(voltage_str)
                except (ValueError, AttributeError):
                    logger.warning(
                        f"Impossibile convertire tensione: {raw_voltage}. "
                        "Impostato valore default 230V"
                    )
                    connection_voltage = 230
            else:
                connection_voltage = 230
                logger.info("Tensione non presente, impostato valore default 230V")

            # Gestione della potenza nominale
            try:
                nominal_power = float(gaudi_data.get("nominal_power", 0))
            except (ValueError, TypeError):
                logger.warning("Errore conversione potenza nominale, impostato 0")
                nominal_power = 0

            # Gestione della produzione attesa
            try:
                expected_production = float(
                    gaudi_data.get("expected_yearly_production", 0)
                )
            except (ValueError, TypeError):
                logger.warning("Errore conversione produzione attesa, impostato 0")
                expected_production = 0

            # Costruzione del dizionario dei valori iniziali
            initial.update(
                {
                    # Dati identificativi
                    "name": gaudi_data.get("plant_name", "").strip(),
                    "pod_code": gaudi_data.get("pod_code", "").strip(),
                    "gaudi_request_code": gaudi_data.get(
                        "gaudi_request_code", ""
                    ).strip(),
                    "censimp_code": gaudi_data.get("censimp_code", "").strip(),
                    # Dati tecnici
                    "nominal_power": nominal_power,
                    "connection_voltage": connection_voltage,
                    "expected_yearly_production": expected_production,
                    "plant_type": "PRODUCER",  # Impianto fotovoltaico è sempre
                    # produttore
                    # Date
                    "installation_date": dates["installation_date"],
                    "validation_date": dates["validation_date"],
                    "expected_operation_date": dates["expected_operation_date"],
                    # Componenti dell'indirizzo
                    # 'address': address_components['address'],
                    # 'city': address_components['city'],
                    # 'province': address_components['province'],
                    # 'zip_code': address_components['zip_code'],
                    "address": parsed_address.get("address", ""),
                    "city": parsed_address.get("city", ""),
                    "province": parsed_address.get("province", ""),
                    "zip_code": parsed_address.get("zip_code", ""),
                }
            )

            # Log dei valori iniziali per debug
            logger.debug("[INITIAL DATA] Valori iniziali elaborati:")
            for key, value in initial.items():
                logger.debug(f"- {key}: {value} (tipo: {type(value)})")

            return initial

        except Exception as e:
            logger.error(
                f"Errore nell'elaborazione dei dati iniziali: {str(e)}",
                exc_info=True
            )
            # In caso di errore, restituiamo comunque un dizionario con
            # valori di default
            return {
                "name": gaudi_data.get("plant_name", ""),
                "pod_code": gaudi_data.get("pod_code", ""),
                "plant_type": "PRODUCER",
                "nominal_power": 0,
                "connection_voltage": 230,
                "expected_yearly_production": 0,
            }

    # Gestisce la creazione di un nuovo impianto dai dati Gaudì
    def form_valid(self, form):
        try:
            gaudi_data = self.request.session.get("plant_gaudi_data", {})
            logger.debug("Dati Gaudì completi: %s", gaudi_data)

            # Crea l'impianto ma non salvarlo ancora
            plant = form.save(commit=False)
            plant.owner = self.request.user

            # 1. Salva l'indirizzo grezzo originale
            raw_address = gaudi_data.get("address", "").strip()
            if raw_address:
                plant.raw_address = raw_address
                logger.debug("Indirizzo grezzo salvato: %s", raw_address)

            # 2. Gestisci l'indirizzo parsato
            parsed_address = gaudi_data.get("parsed_address", {})
            if parsed_address:
                plant.address = parsed_address.get("address", "").strip()
                plant.city = parsed_address.get("city", "").strip()
                plant.province = parsed_address.get("province", "").strip()
                plant.zip_code = parsed_address.get("zip_code", "").strip()
                logger.debug("Indirizzo parsato: %s", parsed_address)

            # 3. Gestisci la tensione
            if voltage := gaudi_data.get("connection_voltage"):
                try:
                    plant.connection_voltage = str(
                        int(float(str(voltage).replace(",", ".")))
                    )
                    logger.debug("Tensione convertita: %s", plant.connection_voltage)
                except (ValueError, TypeError) as e:
                    logger.error(
                        "Errore conversione tensione '%s': %s", voltage, str(e)
                    )
                    plant.connection_voltage = "230"

            # 4. Imposta i flag di verifica Gaudì
            plant.gaudi_verified = True
            plant.gaudi_verification_date = timezone.now()

            # 5. Estrai gli ID dai dati
            section_id = gaudi_data.get("section_id", "")
            group_id = gaudi_data.get("group_id", "")

            # Estrai ID numerici usando regex
            section_match = (
                re.search(r"SZ_(\d+)_\d+", section_id) if section_id else None
            )
            group_match = re.search(r"GR_(\d+)_\d+_\d+", group_id) if group_id else None

            plant.section_id = section_match.group(1) if section_match else ""
            plant.group_id = group_match.group(1) if group_match else ""

            # 6. Aggiorna gli altri campi dai dati Gaudì
            fields_to_update = {
                "gaudi_request_code": gaudi_data.get("gaudi_request_code", "")[:50],
                "censimp_code": gaudi_data.get("censimp_code", "")[:50],
                "nominal_power": float(
                    str(gaudi_data.get("nominal_power", 0)).replace(",", ".")
                ),
                "expected_yearly_production": gaudi_data.get(
                    "expected_yearly_production", 0
                ),
                "section_type": gaudi_data.get("section_type", "")[:50],
                "remote_disconnect": gaudi_data.get("remote_disconnect", False),
                "active_power": float(
                    str(gaudi_data.get("active_power", 0)).replace(",", ".")
                ),
                "net_power": float(
                    str(gaudi_data.get("net_power", 0)).replace(",", ".")
                ),
                "gross_power": float(
                    str(gaudi_data.get("gross_power", 0)).replace(",", ".")
                ),
                "grid_feed_type": (
                    "TOTAL"
                    if gaudi_data.get("grid_feed_type") == "TOTAL"
                    else "PARTIAL"
                ),
                "has_storage": gaudi_data.get("has_storage", False),
            }

            for field, value in fields_to_update.items():
                if hasattr(plant, field):
                    setattr(plant, field, value)

            # 7. Salva l'impianto
            plant.save()

            # 8. Geocodifica
            geocoded = plant.geocode_address(retry_count=3)
            if not geocoded:
                logger.warning("Geocodifica fallita per l'impianto %s", plant.id)

            # 9. Gestione documento
            temp_doc_id = self.request.session.get("temp_gaudi_doc")
            if temp_doc_id:
                try:
                    temp_doc = Document.objects.get(id=temp_doc_id)
                    temp_doc.type = "GAUDI"
                    temp_doc.plant = plant
                    temp_doc.save()
                    logger.info(
                        "Documento Gaudì ID %s associato all'impianto %s",
                        temp_doc_id,
                        plant.id,
                    )
                except Document.DoesNotExist:
                    logger.warning("Documento temporaneo %s non trovato", temp_doc_id)

            # 10. Pulizia sessione
            self.request.session.pop("plant_gaudi_data", None)
            self.request.session.pop("temp_gaudi_doc", None)

            messages.success(self.request, "Impianto creato con successo")
            return super().form_valid(form)

        except Exception as e:
            logger.error(
                "Errore durante la creazione dell'impianto: %s", str(e), exc_info=True
            )
            messages.error(self.request, "Errore durante la creazione dell'impianto")
            return self.form_invalid(form)

    # def get_initial(self):
    #     """Inizializza i dati del form dai dati Gaudì in sessione"""
    #     initial = super().get_initial()
    #     gaudi_data = self.request.session.get("plant_gaudi_data", {})

    #     logger.debug("[INITIAL DATA] Getting gaudi data from session")
    #     logger.debug(f"[INITIAL DATA] Raw gaudi_data:")
    #     logger.debug(f"- Plant address: {gaudi_data.get('address')}")

    #     # Converti le date
    #     installation_date = self._convert_date_str(
    #         gaudi_data.get("installation_date")
    #     )
    #     validation_date = self._convert_date_str(gaudi_data.get("validation_date"))
    #     expected_operation_date = self._convert_date_str(
    #         gaudi_data.get("expected_operation_date")
    #     )

    #     # Elabora l'indirizzo dell'impianto
    #     full_address = gaudi_data.get("address", "")
    #     address = ""
    #     city = ""
    #     province = ""
    #     zip_code = gaudi_data.get(
    #         "cap", ""
    #     )  # Usiamo il CAP già estratto se disponibile

    #     if full_address:
    #         # Rimuovi eventuali riferimenti a Italia e spazi multipli
    #         clean_address = (
    #             full_address.replace("Italia", "").replace("  ", " ").strip()
    #         )

    #         # Split l'indirizzo in parti
    #         parts = [p.strip() for p in clean_address.split(",")]

    #         # Estrai via e numero civico (primi due elementi)
    #         if len(parts) >= 2:
    #             # Prendi solo via e numero civico
    #             address = f"{parts[0].strip()}, {parts[1].strip()}"
    #         elif parts:
    #             address = parts[0].strip()

    #         # Se il CAP non è stato trovato nei dati Gaudì, cercalo nell'indirizzo
    #         if not zip_code:
    #             cap_match = re.search(r"(\d{5})", clean_address)
    #             if cap_match:
    #                 zip_code = cap_match.group(1)

    #         # Estrai la provincia e la città
    #         for part in parts:
    #             if "(" in part:
    #                 # Estrai la provincia
    #                 prov_match = re.search(r"\(([^)]+)\)", part)
    #                 if prov_match:
    #                     province = prov_match.group(1)
    #                     # Converti la provincia nel codice di due lettere
    #                     province = self._get_province_code(province)

    #                 # Estrai la città rimuovendo la parte tra parentesi e il CAP
    #                 city_part = part.split("(")[0].strip()
    #                 if zip_code:
    #                     city_part = city_part.replace(zip_code, "").strip()
    #                 city_part = re.sub(r"\d+", "", city_part).strip()

    #                 # Gestisci il caso di MIRA duplicato
    #                 if "MIRA" in city_part.upper():
    #                     city = "Mira"
    #                 else:
    #                     # Altrimenti formatta in Title Case
    #                     city = " ".join(w.capitalize() for w in city_part.split())
    #                 break

    #     logger.debug(f"[ADDRESS PROCESSING] Extracted from plant location:")
    #     logger.debug(f"- address: {address}")
    #     logger.debug(f"- city: {city}")
    #     logger.debug(f"- province: {province}")
    #     logger.debug(f"- zip_code: {zip_code}")

    #     initial.update(
    #         {
    #             "name": gaudi_data.get("plant_name", ""),
    #             "pod_code": gaudi_data.get("pod_code", ""),
    #             "nominal_power": gaudi_data.get("nominal_power", 0),
    #             "connection_voltage": gaudi_data.get("connection_voltage", ""),
    #             "address": address,
    #             "city": city,
    #             "province": province,
    #             "zip_code": zip_code,
    #             "plant_type": "PRODUCER",  # Impianto fotovoltaico è sempre produttore
    #             "installation_date": installation_date,
    #             "validation_date": validation_date,
    #             "expected_operation_date": expected_operation_date,
    #             "gaudi_request_code": gaudi_data.get("gaudi_request_code", ""),
    #             "censimp_code": gaudi_data.get("censimp_code", ""),
    #             "expected_yearly_production": gaudi_data.get(
    #                 "expected_yearly_production", 0
    #             ),
    #         }
    #     )

    #     logger.debug(f"[INITIAL DATA] Final initial data: {initial}")
    #     return initial

    # def get_context_data(self, **kwargs):
    #     """Aggiunge i dati Gaudì al contesto del template"""
    #     context = super().get_context_data(**kwargs)

    #     # Recupera i dati Gaudì dalla sessione
    #     gaudi_data = self.request.session.get("plant_gaudi_data", {}).copy()

    #     # Pulisci l'indirizzo per la visualizzazione
    #     if gaudi_data.get("address"):
    #         raw_address = gaudi_data["address"]
    #         # Rimuovi le parti duplicate e superflue
    #         clean_address = raw_address.replace("Italia", "")
    #         # Rimuovi il CAP
    #         if gaudi_data.get("cap"):
    #             clean_address = clean_address.replace(gaudi_data["cap"], "")
    #         # Rimuovi la parte tra parentesi e MIRA duplicato
    #         clean_address = re.sub(r"\s+MIRA\s+\(VENEZIA\)", "", clean_address)
    #         clean_address = re.sub(r"\s+MIRA\s+MIRA", " MIRA", clean_address)
    #         # Rimuovi spazi multipli e virgole ripetute
    #         clean_address = re.sub(r"\s+", " ", clean_address)
    #         clean_address = re.sub(r",\s*,", ",", clean_address)
    #         clean_address = clean_address.strip(" ,")

    #         # Aggiorna l'indirizzo nei dati
    #         gaudi_data["address"] = clean_address

    #     # Aggiungi i dati Gaudì al contesto
    #     context["gaudi_data"] = gaudi_data

    #     # Il resto del codice rimane invariato...
    #     if settings.DEBUG:
    #         context["debug"] = {
    #             "initial_data": self.get_initial(),
    #             "form_data": self.get_form().initial if self.get_form() else None,
    #             "raw_gaudi_data": gaudi_data,
    #         }

    #     context.update(
    #         {
    #             "title": "Nuovo Impianto da Attestato Gaudì",
    #             "submit_label": "Crea Impianto",
    #             "can_edit_gaudi_data": False,
    #             "show_gaudi_preview": True,
    #         }
    #     )

    #     return context
