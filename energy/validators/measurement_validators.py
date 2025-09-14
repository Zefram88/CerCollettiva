# energy/validators/measurement_validators.py
"""
Validatori Pydantic per misurazioni - TS-02.1.1
Sistema centralizzato di validazione input per prevenire injection e corruzione dati
"""

from datetime import datetime

# from decimal import Decimal
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, validator


class MeasurementCreateValidator(BaseModel):
    """Validatore per creazione misurazioni"""

    device_id: int = Field(..., gt=0, description="ID dispositivo")
    plant_id: int = Field(..., gt=0, description="ID impianto")
    measurement_type: Literal[
        "DRAWN_POWER",
        "DRAWN_ENERGY",
        "INJECTED_POWER",
        "INJECTED_ENERGY",
        "PRODUCTION_POWER",
        "PRODUCTION_ENERGY",
    ] = Field(..., description="Tipo misurazione")
    power: float = Field(..., ge=-1000000, le=1000000, description="Potenza in W")
    voltage: float = Field(..., ge=0, le=500, description="Tensione in V")
    current: float = Field(..., ge=-1000, le=1000, description="Corrente in A")
    energy_total: float = Field(0, ge=0, description="Energia totale in kWh")
    energy: float = Field(0, ge=0, description="Energia in kWh")
    frequency: Optional[float] = Field(50, ge=45, le=65, description="Frequenza in Hz")
    power_factor: Optional[float] = Field(
        None, ge=-1, le=1, description="Fattore di potenza"
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Dati grezzi JSON"
    )
    timestamp: Optional[datetime] = Field(None, description="Timestamp misurazione")

    @validator("power")
    def validate_power(cls, v):
        """Valida la potenza"""
        if not isinstance(v, (int, float)):
            raise ValueError("Potenza deve essere un numero")

        if abs(v) > 1000000:
            raise ValueError("Potenza non può superare ±1MW")

        return float(v)

    @validator("voltage")
    def validate_voltage(cls, v):
        """Valida la tensione"""
        if not isinstance(v, (int, float)):
            raise ValueError("Tensione deve essere un numero")

        if v < 0 or v > 500:
            raise ValueError("Tensione deve essere tra 0 e 500V")

        return float(v)

    @validator("current")
    def validate_current(cls, v):
        """Valida la corrente"""
        if not isinstance(v, (int, float)):
            raise ValueError("Corrente deve essere un numero")

        if v < -1000 or v > 1000:
            raise ValueError("Corrente deve essere tra -1000 e 1000A")

        return float(v)

    @validator("energy_total")
    def validate_energy_total(cls, v):
        """Valida l'energia totale"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Energia totale deve essere un numero")

            if v < 0:
                raise ValueError("Energia totale non può essere negativa")

            return float(v)
        return v

    @validator("energy")
    def validate_energy(cls, v):
        """Valida l'energia"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Energia deve essere un numero")

            if v < 0:
                raise ValueError("Energia non può essere negativa")

            return float(v)
        return v

    @validator("frequency")
    def validate_frequency(cls, v):
        """Valida la frequenza"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Frequenza deve essere un numero")

            if v < 45 or v > 65:
                raise ValueError("Frequenza deve essere tra 45 e 65 Hz")

            return float(v)
        return v

    @validator("power_factor")
    def validate_power_factor(cls, v):
        """Valida il fattore di potenza"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Fattore di potenza deve essere un numero")

            if v < -1 or v > 1:
                raise ValueError("Fattore di potenza deve essere tra -1 e 1")

            return float(v)
        return v

    @validator("raw_data")
    def validate_raw_data(cls, v):
        """Valida i dati grezzi"""
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Dati grezzi devono essere un dizionario")

            # Prevenire injection nei dati JSON
            for key, value in v.items():
                if isinstance(key, str) and any(
                    char in key for char in ["<", ">", "script", "javascript:"]
                ):
                    raise ValueError("Chiave dati grezzi contiene caratteri non validi")

                if isinstance(value, str) and any(
                    char in value for char in ["<script", "javascript:", "data:"]
                ):
                    raise ValueError("Valore dati grezzi contiene caratteri non validi")

            return v
        return v


class MeasurementUpdateValidator(BaseModel):
    """Validatore per aggiornamento misurazioni"""

    device_id: Optional[int] = Field(None, gt=0)
    plant_id: Optional[int] = Field(None, gt=0)
    measurement_type: Optional[
        Literal[
            "DRAWN_POWER",
            "DRAWN_ENERGY",
            "INJECTED_POWER",
            "INJECTED_ENERGY",
            "PRODUCTION_POWER",
            "PRODUCTION_ENERGY",
        ]
    ] = None
    power: Optional[float] = Field(None, ge=-1000000, le=1000000)
    voltage: Optional[float] = Field(None, ge=0, le=500)
    current: Optional[float] = Field(None, ge=-1000, le=1000)
    energy_total: Optional[float] = Field(None, ge=0)
    energy: Optional[float] = Field(None, ge=0)
    frequency: Optional[float] = Field(None, ge=45, le=65)
    power_factor: Optional[float] = Field(None, ge=-1, le=1)
    raw_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None

    @validator("power")
    def validate_power(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Potenza deve essere un numero")
            if abs(v) > 1000000:
                raise ValueError("Potenza non può superare ±1MW")
            return float(v)
        return v

    @validator("voltage")
    def validate_voltage(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Tensione deve essere un numero")
            if v < 0 or v > 500:
                raise ValueError("Tensione deve essere tra 0 e 500V")
            return float(v)
        return v

    @validator("current")
    def validate_current(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Corrente deve essere un numero")
            if v < -1000 or v > 1000:
                raise ValueError("Corrente deve essere tra -1000 e 1000A")
            return float(v)
        return v

    @validator("energy_total")
    def validate_energy_total(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Energia totale deve essere un numero")
            if v < 0:
                raise ValueError("Energia totale non può essere negativa")
            return float(v)
        return v

    @validator("energy")
    def validate_energy(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Energia deve essere un numero")
            if v < 0:
                raise ValueError("Energia non può essere negativa")
            return float(v)
        return v

    @validator("frequency")
    def validate_frequency(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Frequenza deve essere un numero")
            if v < 45 or v > 65:
                raise ValueError("Frequenza deve essere tra 45 e 65 Hz")
            return float(v)
        return v

    @validator("power_factor")
    def validate_power_factor(cls, v):
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Fattore di potenza deve essere un numero")
            if v < -1 or v > 1:
                raise ValueError("Fattore di potenza deve essere tra -1 e 1")
            return float(v)
        return v

    @validator("raw_data")
    def validate_raw_data(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("Dati grezzi devono essere un dizionario")

            for key, value in v.items():
                if isinstance(key, str) and any(
                    char in key for char in ["<", ">", "script", "javascript:"]
                ):
                    raise ValueError("Chiave dati grezzi contiene caratteri non validi")
                if isinstance(value, str) and any(
                    char in value for char in ["<script", "javascript:", "data:"]
                ):
                    raise ValueError("Valore dati grezzi contiene caratteri non validi")

            return v
        return v


class DeviceMeasurementDetailValidator(BaseModel):
    """Validatore per dettagli misurazione per fase"""

    measurement_id: int = Field(..., gt=0, description="ID misurazione")
    phase: Literal["a", "b", "c", "n"] = Field(..., description="Fase")
    voltage: float = Field(..., ge=0, le=500, description="Tensione di fase in V")
    current: float = Field(..., ge=-1000, le=1000, description="Corrente di fase in A")
    power: float = Field(
        ..., ge=-1000000, le=1000000, description="Potenza di fase in W"
    )
    power_factor: Optional[float] = Field(
        None, ge=-1, le=1, description="Fattore di potenza di fase"
    )
    frequency: float = Field(50, ge=45, le=65, description="Frequenza in Hz")

    @validator("voltage")
    def validate_voltage(cls, v):
        """Valida la tensione di fase"""
        if not isinstance(v, (int, float)):
            raise ValueError("Tensione deve essere un numero")

        if v < 0 or v > 500:
            raise ValueError("Tensione deve essere tra 0 e 500V")

        return float(v)

    @validator("current")
    def validate_current(cls, v):
        """Valida la corrente di fase"""
        if not isinstance(v, (int, float)):
            raise ValueError("Corrente deve essere un numero")

        if v < -1000 or v > 1000:
            raise ValueError("Corrente deve essere tra -1000 e 1000A")

        return float(v)

    @validator("power")
    def validate_power(cls, v):
        """Valida la potenza di fase"""
        if not isinstance(v, (int, float)):
            raise ValueError("Potenza deve essere un numero")

        if abs(v) > 1000000:
            raise ValueError("Potenza non può superare ±1MW")

        return float(v)

    @validator("power_factor")
    def validate_power_factor(cls, v):
        """Valida il fattore di potenza di fase"""
        if v is not None:
            if not isinstance(v, (int, float)):
                raise ValueError("Fattore di potenza deve essere un numero")

            if v < -1 or v > 1:
                raise ValueError("Fattore di potenza deve essere tra -1 e 1")

            return float(v)
        return v

    @validator("frequency")
    def validate_frequency(cls, v):
        """Valida la frequenza"""
        if not isinstance(v, (int, float)):
            raise ValueError("Frequenza deve essere un numero")

        if v < 45 or v > 65:
            raise ValueError("Frequenza deve essere tra 45 e 65 Hz")

        return float(v)

    @validator("phase")
    def validate_phase(cls, v):
        """Valida la fase"""
        if v not in ["a", "b", "c", "n"]:
            raise ValueError("Fase deve essere a, b, c o n")
        return v.lower()
