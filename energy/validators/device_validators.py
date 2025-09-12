# energy/validators/device_validators.py
"""
Validatori Pydantic per dispositivi - TS-02.1.1
Sistema centralizzato di validazione input per prevenire injection e corruzione dati
"""

from pydantic import BaseModel, validator, Field
from typing import Optional, Literal
from datetime import date
import re

class DeviceCreateValidator(BaseModel):
    """Validatore per creazione dispositivi"""
    name: str = Field(..., min_length=3, max_length=100, description="Nome del dispositivo")
    device_type: str = Field(..., min_length=2, max_length=50, description="Tipo dispositivo")
    serial_number: str = Field(..., min_length=1, max_length=100, description="Numero seriale")
    description: Optional[str] = Field(None, max_length=500, description="Descrizione opzionale")
    installation_date: date = Field(..., description="Data di installazione")
    is_active: bool = Field(True, description="Dispositivo attivo")
    mqtt_topic_override: Optional[str] = Field(None, max_length=255, description="Override topic MQTT")
    
    @validator('name')
    def validate_name(cls, v):
        """Valida il nome del dispositivo"""
        if not v or len(v.strip()) < 3:
            raise ValueError('Nome deve essere di almeno 3 caratteri')
        
        # Prevenire XSS
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Nome contiene caratteri non validi')
        
        return v.strip()
    
    @validator('device_type')
    def validate_device_type(cls, v):
        """Valida il tipo di dispositivo"""
        allowed_types = [
            'SHELLY_PRO_3EM', 'SHELLY_PRO_EM', 'SHELLY_EM3', 
            'SHELLY_EM', 'SHELLY_PLUS_PM', 'CUSTOM'
        ]
        if v.upper() not in allowed_types:
            raise ValueError(f'Tipo dispositivo non valido. Consentiti: {", ".join(allowed_types)}')
        return v.upper()
    
    @validator('serial_number')
    def validate_serial_number(cls, v):
        """Valida il numero seriale"""
        if not v or len(v.strip()) < 1:
            raise ValueError('Numero seriale obbligatorio')
        
        # Solo caratteri alfanumerici, underscore e trattini
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Numero seriale può contenere solo lettere, numeri, underscore e trattini')
        
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Valida la descrizione"""
        if v is not None:
            # Prevenire injection
            if any(char in v for char in [';', '--', '/*', '*/', '<script', 'javascript:']):
                raise ValueError('Descrizione contiene caratteri non validi')
            return v.strip() if v.strip() else None
        return v
    
    @validator('mqtt_topic_override')
    def validate_mqtt_topic(cls, v):
        """Valida il topic MQTT"""
        if v is not None:
            if len(v.strip()) == 0:
                return None
            
            # Prevenire injection MQTT
            if any(char in v for char in ['#', '+', '$', ' ', '\n', '\r', '\t']):
                raise ValueError('Topic MQTT contiene caratteri non validi')
            
            return v.strip()
        return v

class DeviceUpdateValidator(BaseModel):
    """Validatore per aggiornamento dispositivi"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    device_type: Optional[str] = Field(None, min_length=2, max_length=50)
    serial_number: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    installation_date: Optional[date] = None
    is_active: Optional[bool] = None
    mqtt_topic_override: Optional[str] = Field(None, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('Nome deve essere di almeno 3 caratteri')
            if '<' in v or '>' in v or 'script' in v.lower():
                raise ValueError('Nome contiene caratteri non validi')
            return v.strip()
        return v
    
    @validator('device_type')
    def validate_device_type(cls, v):
        if v is not None:
            allowed_types = [
                'SHELLY_PRO_3EM', 'SHELLY_PRO_EM', 'SHELLY_EM3', 
                'SHELLY_EM', 'SHELLY_PLUS_PM', 'CUSTOM'
            ]
            if v.upper() not in allowed_types:
                raise ValueError(f'Tipo dispositivo non valido. Consentiti: {", ".join(allowed_types)}')
            return v.upper()
        return v
    
    @validator('serial_number')
    def validate_serial_number(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Numero seriale obbligatorio')
            if not re.match(r'^[A-Za-z0-9_-]+$', v):
                raise ValueError('Numero seriale può contenere solo lettere, numeri, underscore e trattini')
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            if any(char in v for char in [';', '--', '/*', '*/', '<script', 'javascript:']):
                raise ValueError('Descrizione contiene caratteri non validi')
            return v.strip() if v.strip() else None
        return v
    
    @validator('mqtt_topic_override')
    def validate_mqtt_topic(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                return None
            if any(char in v for char in ['#', '+', '$', ' ', '\n', '\r', '\t']):
                raise ValueError('Topic MQTT contiene caratteri non validi')
            return v.strip()
        return v

class DeviceConfigurationCreateValidator(BaseModel):
    """Validatore per creazione configurazione dispositivi"""
    device_id: str = Field(..., min_length=1, max_length=100, description="ID dispositivo")
    name: str = Field(..., min_length=1, max_length=100, description="Nome dispositivo")
    device_type: Literal[
        'SHELLY_PRO_3EM', 'SHELLY_PRO_EM', 'SHELLY_EM3', 
        'SHELLY_EM', 'SHELLY_PLUS_PM', 'CUSTOM'
    ] = Field(..., description="Tipo dispositivo")
    vendor: Literal['SHELLY', 'CUSTOM'] = Field(..., description="Vendor")
    model: str = Field(..., min_length=1, max_length=50, description="Modello")
    plant_id: int = Field(..., gt=0, description="ID impianto")
    mqtt_topic_template: Optional[str] = Field(None, max_length=255, description="Template topic MQTT")
    firmware_version: Optional[str] = Field(None, max_length=50, description="Versione firmware")
    is_active: bool = Field(True, description="Dispositivo attivo")
    
    @validator('device_id')
    def validate_device_id(cls, v):
        """Valida l'ID del dispositivo"""
        if not v or len(v.strip()) < 1:
            raise ValueError('ID dispositivo obbligatorio')
        
        # Solo caratteri alfanumerici, underscore e trattini
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('ID dispositivo può contenere solo lettere, numeri, underscore e trattini')
        
        return v.strip()
    
    @validator('name')
    def validate_name(cls, v):
        """Valida il nome"""
        if not v or len(v.strip()) < 1:
            raise ValueError('Nome obbligatorio')
        
        # Prevenire XSS
        if '<' in v or '>' in v or 'script' in v.lower():
            raise ValueError('Nome contiene caratteri non validi')
        
        return v.strip()
    
    @validator('model')
    def validate_model(cls, v):
        """Valida il modello"""
        if not v or len(v.strip()) < 1:
            raise ValueError('Modello obbligatorio')
        
        # Solo caratteri alfanumerici, underscore e trattini
        if not re.match(r'^[A-Za-z0-9_-]+$', v):
            raise ValueError('Modello può contenere solo lettere, numeri, underscore e trattini')
        
        return v.strip()
    
    @validator('mqtt_topic_template')
    def validate_mqtt_topic_template(cls, v):
        """Valida il template topic MQTT"""
        if v is not None:
            if len(v.strip()) == 0:
                return None
            
            # Prevenire injection MQTT
            if any(char in v for char in ['#', '+', '$', ' ', '\n', '\r', '\t']):
                raise ValueError('Template topic MQTT contiene caratteri non validi')
            
            return v.strip()
        return v
    
    @validator('firmware_version')
    def validate_firmware_version(cls, v):
        """Valida la versione firmware"""
        if v is not None:
            if len(v.strip()) == 0:
                return None
            
            # Formato versione: x.y.z o x.y
            if not re.match(r'^\d+\.\d+(\.\d+)?$', v.strip()):
                raise ValueError('Formato versione firmware non valido (es. 1.2.3 o 1.2)')
            
            return v.strip()
        return v

class DeviceConfigurationUpdateValidator(BaseModel):
    """Validatore per aggiornamento configurazione dispositivi"""
    device_id: Optional[str] = Field(None, min_length=1, max_length=100)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    device_type: Optional[Literal[
        'SHELLY_PRO_3EM', 'SHELLY_PRO_EM', 'SHELLY_EM3', 
        'SHELLY_EM', 'SHELLY_PLUS_PM', 'CUSTOM'
    ]] = None
    vendor: Optional[Literal['SHELLY', 'CUSTOM']] = None
    model: Optional[str] = Field(None, min_length=1, max_length=50)
    plant_id: Optional[int] = Field(None, gt=0)
    mqtt_topic_template: Optional[str] = Field(None, max_length=255)
    firmware_version: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    
    @validator('device_id')
    def validate_device_id(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('ID dispositivo obbligatorio')
            if not re.match(r'^[A-Za-z0-9_-]+$', v):
                raise ValueError('ID dispositivo può contenere solo lettere, numeri, underscore e trattini')
            return v.strip()
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Nome obbligatorio')
            if '<' in v or '>' in v or 'script' in v.lower():
                raise ValueError('Nome contiene caratteri non validi')
            return v.strip()
        return v
    
    @validator('model')
    def validate_model(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Modello obbligatorio')
            if not re.match(r'^[A-Za-z0-9_-]+$', v):
                raise ValueError('Modello può contenere solo lettere, numeri, underscore e trattini')
            return v.strip()
        return v
    
    @validator('mqtt_topic_template')
    def validate_mqtt_topic_template(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                return None
            if any(char in v for char in ['#', '+', '$', ' ', '\n', '\r', '\t']):
                raise ValueError('Template topic MQTT contiene caratteri non validi')
            return v.strip()
        return v
    
    @validator('firmware_version')
    def validate_firmware_version(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                return None
            if not re.match(r'^\d+\.\d+(\.\d+)?$', v.strip()):
                raise ValueError('Formato versione firmware non valido (es. 1.2.3 o 1.2)')
            return v.strip()
        return v
