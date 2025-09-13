# documents/validators/document_validators.py
"""
Validatori Pydantic per documenti - TS-02.1.1
Sistema centralizzato di validazione input per prevenire injection e corruzione dati
"""

import re
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator


class DocumentCreateValidator(BaseModel):
    """Validatore per creazione documenti"""

    type: Literal[
        "BILL",
        "SYSTEM_CERT",
        "GSE_DOC",
        "PANELS_PHOTO",
        "INVERTER_PHOTO",
        "PANELS_LIST",
        "ID_DOC",
        "GAUDI",
        "OTHER",
    ] = Field(..., description="Tipo documento")
    source: Literal["USER", "SYSTEM"] = Field("USER", description="Origine documento")
    notes: Optional[str] = Field(None, max_length=1000, description="Note opzionali")
    plant_id: Optional[int] = Field(None, gt=0, description="ID impianto associato")
    data_classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PERSONAL"] = (
        Field("INTERNAL", description="Classificazione dati")
    )
    gdpr_consent: bool = Field(False, description="Consenso GDPR")
    retention_date: Optional[date] = Field(None, description="Data di conservazione")

    @validator("notes")
    def validate_notes(cls, v):
        """Valida le note del documento"""
        if v is not None:
            # Prevenire XSS e injection
            if any(char in v for char in ["<", ">", "script", "javascript:", "data:"]):
                raise ValueError("Note contiene caratteri non validi")

            # Prevenire SQL injection
            if any(
                pattern in v.lower()
                for pattern in [
                    ";",
                    "--",
                    "/*",
                    "*/",
                    "drop",
                    "delete",
                    "insert",
                    "update",
                ]
            ):
                raise ValueError("Note contiene caratteri non validi")

            return v.strip() if v.strip() else None
        return v

    @validator("type")
    def validate_type(cls, v):
        """Valida il tipo di documento"""
        allowed_types = [
            "BILL",
            "SYSTEM_CERT",
            "GSE_DOC",
            "PANELS_PHOTO",
            "INVERTER_PHOTO",
            "PANELS_LIST",
            "ID_DOC",
            "GAUDI",
            "OTHER",
        ]
        if v not in allowed_types:
            raise ValueError(
                f'Tipo documento non valido. Consentiti: {", ".join(allowed_types)}'
            )
        return v

    @validator("data_classification")
    def validate_data_classification(cls, v):
        """Valida la classificazione dati"""
        allowed_classifications = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PERSONAL"]
        if v not in allowed_classifications:
            raise ValueError(
                f'Classificazione dati non valida. Consentite: '
                f'{", ".join(allowed_classifications)}'
            )
        return v

    @validator("gdpr_consent")
    def validate_gdpr_consent(cls, v, values):
        """Valida il consenso GDPR per documenti con dati personali"""
        doc_type = values.get("type")
        data_classification = values.get("data_classification")

        # Documenti che richiedono consenso GDPR
        requires_consent = (
            doc_type in ["ID_DOC", "BILL"] or data_classification == "PERSONAL"
        )

        if requires_consent and not v:
            raise ValueError("Consenso GDPR obbligatorio per questo tipo di documento")

        return v

    @validator("retention_date")
    def validate_retention_date(cls, v, values):
        """Valida la data di conservazione"""
        if v is not None:
            # La data di conservazione non può essere nel passato
            if v < date.today():
                raise ValueError("Data di conservazione non può essere nel passato")

            # La data di conservazione non può essere troppo lontana nel
            # futuro (max 50 anni)
            max_future_date = date.today().replace(year=date.today().year + 50)
            if v > max_future_date:
                raise ValueError(
                    "Data di conservazione non può essere oltre 50 anni nel futuro"
                )

        return v


class DocumentUpdateValidator(BaseModel):
    """Validatore per aggiornamento documenti"""

    type: Optional[
        Literal[
            "BILL",
            "SYSTEM_CERT",
            "GSE_DOC",
            "PANELS_PHOTO",
            "INVERTER_PHOTO",
            "PANELS_LIST",
            "ID_DOC",
            "GAUDI",
            "OTHER",
        ]
    ] = None
    source: Optional[Literal["USER", "SYSTEM"]] = None
    notes: Optional[str] = Field(None, max_length=1000)
    plant_id: Optional[int] = Field(None, gt=0)
    data_classification: Optional[
        Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PERSONAL"]
    ] = None
    gdpr_consent: Optional[bool] = None
    retention_date: Optional[date] = None
    processing_status: Optional[
        Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    ] = None

    @validator("notes")
    def validate_notes(cls, v):
        if v is not None:
            if any(char in v for char in ["<", ">", "script", "javascript:", "data:"]):
                raise ValueError("Note contiene caratteri non validi")
            if any(
                pattern in v.lower()
                for pattern in [
                    ";",
                    "--",
                    "/*",
                    "*/",
                    "drop",
                    "delete",
                    "insert",
                    "update",
                ]
            ):
                raise ValueError("Note contiene caratteri non validi")
            return v.strip() if v.strip() else None
        return v

    @validator("type")
    def validate_type(cls, v):
        if v is not None:
            allowed_types = [
                "BILL",
                "SYSTEM_CERT",
                "GSE_DOC",
                "PANELS_PHOTO",
                "INVERTER_PHOTO",
                "PANELS_LIST",
                "ID_DOC",
                "GAUDI",
                "OTHER",
            ]
            if v not in allowed_types:
                raise ValueError(
                    f'Tipo documento non valido. Consentiti: {", ".join(allowed_types)}'
                )
        return v

    @validator("data_classification")
    def validate_data_classification(cls, v):
        if v is not None:
            allowed_classifications = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PERSONAL"]
            if v not in allowed_classifications:
                raise ValueError(
                    f'Classificazione dati non valida. Consentite: '
                    f'{", ".join(allowed_classifications)}'
                )
        return v

    @validator("gdpr_consent")
    def validate_gdpr_consent(cls, v, values):
        if v is not None:
            doc_type = values.get("type")
            data_classification = values.get("data_classification")

            requires_consent = (
                doc_type in ["ID_DOC", "BILL"] or data_classification == "PERSONAL"
            )

            if requires_consent and not v:
                raise ValueError(
                    "Consenso GDPR obbligatorio per questo tipo di documento"
                )

        return v

    @validator("retention_date")
    def validate_retention_date(cls, v):
        if v is not None:
            if v < date.today():
                raise ValueError("Data di conservazione non può essere nel passato")

            max_future_date = date.today().replace(year=date.today().year + 50)
            if v > max_future_date:
                raise ValueError(
                    "Data di conservazione non può essere oltre 50 anni nel futuro"
                )

        return v

    @validator("processing_status")
    def validate_processing_status(cls, v):
        if v is not None:
            allowed_statuses = ["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
            if v not in allowed_statuses:
                raise ValueError(
                    f'Stato elaborazione non valido. Consentiti: '
                    f'{", ".join(allowed_statuses)}'
                )
        return v


class DocumentAccessValidator(BaseModel):
    """Validatore per accessi ai documenti"""

    document_id: int = Field(..., gt=0, description="ID documento")
    accessed_by_id: int = Field(..., gt=0, description="ID utente che accede")
    access_ip: Optional[str] = Field(None, description="IP di accesso")
    access_timestamp: Optional[datetime] = Field(None, description="Timestamp accesso")

    @validator("access_ip")
    def validate_access_ip(cls, v):
        """Valida l'IP di accesso"""
        if v is not None:
            # Validazione formato IP (IPv4 o IPv6)
            ipv4_pattern = (
                r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            )
            ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"

            if not (re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v)):
                raise ValueError("Formato IP non valido")

            # Prevenire IP privati o localhost in produzione (opzionale)
            if v in ["127.0.0.1", "localhost", "0.0.0.0"]:
                raise ValueError("IP non valido per accesso")

        return v

    @validator("access_timestamp")
    def validate_access_timestamp(cls, v):
        """Valida il timestamp di accesso"""
        if v is not None:
            # Il timestamp non può essere nel futuro
            if v > datetime.now():
                raise ValueError("Timestamp accesso non può essere nel futuro")

            # Il timestamp non può essere troppo nel passato (max 1 anno)
            from datetime import timedelta

            min_past_date = datetime.now() - timedelta(days=365)
            if v < min_past_date:
                raise ValueError("Timestamp accesso troppo nel passato")

        return v


class DocumentFileValidator(BaseModel):
    """Validatore per file di documenti"""

    filename: str = Field(..., min_length=1, max_length=255, description="Nome file")
    content_type: str = Field(..., description="Tipo contenuto")
    size: int = Field(
        ..., ge=1, le=10485760, description="Dimensione file in bytes (max 10MB)"
    )
    checksum: Optional[str] = Field(None, max_length=64, description="Checksum SHA-256")

    @validator("filename")
    def validate_filename(cls, v):
        """Valida il nome del file"""
        if not v or len(v.strip()) < 1:
            raise ValueError("Nome file obbligatorio")

        # Prevenire caratteri pericolosi
        dangerous_chars = ["<", ">", ":", '"', "|", "?", "*", "\\", "/"]
        if any(char in v for char in dangerous_chars):
            raise ValueError("Nome file contiene caratteri non validi")

        # Prevenire path traversal
        if ".." in v or v.startswith("/") or v.startswith("\\"):
            raise ValueError("Nome file non sicuro")

        # Prevenire estensioni pericolose
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".scr",
            ".com",
            ".pif",
            ".vbs",
            ".js",
        ]
        if any(v.lower().endswith(ext) for ext in dangerous_extensions):
            raise ValueError("Tipo di file non consentito")

        return v.strip()

    @validator("content_type")
    def validate_content_type(cls, v):
        """Valida il tipo di contenuto"""
        allowed_types = [
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ]

        if v not in allowed_types:
            raise ValueError(
                f'Tipo contenuto non consentito. Consentiti: {", ".join(allowed_types)}'
            )

        return v

    @validator("size")
    def validate_size(cls, v):
        """Valida la dimensione del file"""
        if v <= 0:
            raise ValueError("Dimensione file deve essere maggiore di 0")

        if v > 10485760:  # 10MB
            raise ValueError("Dimensione file non può superare 10MB")

        return v

    @validator("checksum")
    def validate_checksum(cls, v):
        """Valida il checksum SHA-256"""
        if v is not None:
            if len(v) != 64:
                raise ValueError("Checksum deve essere di 64 caratteri (SHA-256)")

            if not re.match(r"^[a-f0-9]{64}$", v.lower()):
                raise ValueError("Checksum deve contenere solo caratteri esadecimali")

        return v


class DocumentSearchValidator(BaseModel):
    """Validatore per ricerca documenti"""

    query: Optional[str] = Field(None, max_length=100, description="Query di ricerca")
    document_type: Optional[
        Literal[
            "BILL",
            "SYSTEM_CERT",
            "GSE_DOC",
            "PANELS_PHOTO",
            "INVERTER_PHOTO",
            "PANELS_LIST",
            "ID_DOC",
            "GAUDI",
            "OTHER",
        ]
    ] = None
    data_classification: Optional[
        Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "PERSONAL"]
    ] = None
    plant_id: Optional[int] = Field(None, gt=0)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: int = Field(50, ge=1, le=100, description="Limite risultati")
    offset: int = Field(0, ge=0, description="Offset risultati")

    @validator("query")
    def validate_query(cls, v):
        """Valida la query di ricerca"""
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("Query di ricerca deve essere di almeno 2 caratteri")

            # Prevenire injection nella query
            if any(char in v for char in ["<", ">", "script", "javascript:", "data:"]):
                raise ValueError("Query contiene caratteri non validi")

            # Prevenire SQL injection
            if any(
                pattern in v.lower()
                for pattern in [
                    ";",
                    "--",
                    "/*",
                    "*/",
                    "union",
                    "select",
                    "insert",
                    "update",
                    "delete",
                ]
            ):
                raise ValueError("Query contiene caratteri non validi")

            return v.strip()
        return v

    @validator("date_from")
    def validate_date_from(cls, v):
        """Valida la data di inizio"""
        if v is not None:
            if v > date.today():
                raise ValueError("Data di inizio non può essere nel futuro")
        return v

    @validator("date_to")
    def validate_date_to(cls, v, values):
        """Valida la data di fine"""
        if v is not None:
            if v > date.today():
                raise ValueError("Data di fine non può essere nel futuro")

            date_from = values.get("date_from")
            if date_from and v < date_from:
                raise ValueError(
                    "Data di fine non può essere anteriore alla data di inizio"
                )

        return v
