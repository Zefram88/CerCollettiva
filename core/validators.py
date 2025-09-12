# core/validators.py
"""
Framework di validazione riutilizzabile per CerCollettiva
Consolida pattern di validazione duplicati in un sistema centralizzato
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import re
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseValidator:
    """Classe base per validatori riutilizzabili"""
    
    def __init__(self, field_name=None, error_message=None):
        self.field_name = field_name
        self.error_message = error_message or self.get_default_error_message()
    
    def get_default_error_message(self):
        """Override per personalizzare il messaggio di errore"""
        return _("Valore non valido")
    
    def validate(self, value, cleaned_data=None):
        """Metodo principale di validazione - da implementare nelle sottoclassi"""
        raise NotImplementedError("Subclasses must implement validate method")
    
    def __call__(self, value, cleaned_data=None):
        """Chiamata del validatore"""
        try:
            return self.validate(value, cleaned_data)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Validation error in {self.__class__.__name__}: {str(e)}")
            raise ValidationError(self.error_message)


class PODCodeValidator(BaseValidator):
    """Validatore per codici POD italiani"""
    
    def get_default_error_message(self):
        return _("Il codice POD deve iniziare con 'IT' e avere 14-15 caratteri")
    
    def validate(self, value, cleaned_data=None):
        if not value:
            return value
            
        value = value.upper().strip()
        
        # Verifica formato base
        if not value.startswith('IT'):
            raise ValidationError(_("Il codice POD deve iniziare con 'IT'"))
        
        if len(value) < 14 or len(value) > 15:
            raise ValidationError(_("Il codice POD deve avere 14-15 caratteri"))
        
        # Verifica caratteri validi (lettere e numeri)
        if not re.match(r'^IT[A-Z0-9]+$', value):
            raise ValidationError(_("Il codice POD può contenere solo lettere e numeri"))
        
        return value


class PowerValidator(BaseValidator):
    """Validatore per valori di potenza"""
    
    def __init__(self, min_value=0, max_value=None, field_name=None):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(field_name)
    
    def get_default_error_message(self):
        if self.max_value:
            return _("La potenza deve essere tra {min} e {max} kW").format(
                min=self.min_value, max=self.max_value
            )
        return _("La potenza deve essere maggiore di {min} kW").format(min=self.min_value)
    
    def validate(self, value, cleaned_data=None):
        if value is None:
            return value
            
        if value < self.min_value:
            raise ValidationError(_("La potenza deve essere maggiore di {min} kW").format(min=self.min_value))
        
        if self.max_value and value > self.max_value:
            raise ValidationError(_("La potenza non può superare {max} kW").format(max=self.max_value))
        
        return value


class EmailUniquenessValidator(BaseValidator):
    """Validatore per email uniche"""
    
    def get_default_error_message(self):
        return _("Un utente con questa email esiste già")
    
    def validate(self, value, cleaned_data=None):
        if not value:
            return value
            
        if User.objects.filter(email=value).exists():
            raise ValidationError(self.error_message)
        
        return value


class UsernameUniquenessValidator(BaseValidator):
    """Validatore per username unici"""
    
    def get_default_error_message(self):
        return _("Un utente con questo nome utente esiste già")
    
    def validate(self, value, cleaned_data=None):
        if not value:
            return value
            
        if User.objects.filter(username=value).exists():
            raise ValidationError(self.error_message)
        
        return value


class FileTypeValidator(BaseValidator):
    """Validatore per tipi di file"""
    
    def __init__(self, allowed_extensions=None, max_size_mb=None, field_name=None):
        self.allowed_extensions = allowed_extensions or []
        self.max_size_mb = max_size_mb
        super().__init__(field_name)
    
    def get_default_error_message(self):
        if self.allowed_extensions:
            return _("File non supportato. Estensioni consentite: {extensions}").format(
                extensions=", ".join(self.allowed_extensions)
            )
        return _("File non supportato")
    
    def validate(self, value, cleaned_data=None):
        if not value:
            return value
        
        # Verifica estensione
        if self.allowed_extensions:
            file_extension = value.name.split('.')[-1].lower()
            if file_extension not in [ext.lower().lstrip('.') for ext in self.allowed_extensions]:
                raise ValidationError(self.error_message)
        
        # Verifica dimensione
        if self.max_size_mb:
            max_size_bytes = self.max_size_mb * 1024 * 1024
            if value.size > max_size_bytes:
                raise ValidationError(_("Il file non può superare {size}MB").format(size=self.max_size_mb))
        
        return value


class ConditionalRequiredValidator(BaseValidator):
    """Validatore per campi condizionalmente obbligatori"""
    
    def __init__(self, condition_field, condition_value, field_name=None):
        self.condition_field = condition_field
        self.condition_value = condition_value
        super().__init__(field_name)
    
    def get_default_error_message(self):
        return _("Questo campo è obbligatorio")
    
    def validate(self, value, cleaned_data=None):
        if not cleaned_data:
            return value
        
        condition_met = cleaned_data.get(self.condition_field) == self.condition_value
        
        if condition_met and not value:
            raise ValidationError(self.error_message)
        
        return value


class DateRangeValidator(BaseValidator):
    """Validatore per range di date"""
    
    def __init__(self, start_date_field=None, end_date_field=None, field_name=None):
        self.start_date_field = start_date_field
        self.end_date_field = end_date_field
        super().__init__(field_name)
    
    def get_default_error_message(self):
        return _("Date non valide")
    
    def validate(self, value, cleaned_data=None):
        if not cleaned_data or not value:
            return value
        
        start_date = cleaned_data.get(self.start_date_field)
        end_date = cleaned_data.get(self.end_date_field)
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError(_("La data di fine non può essere anteriore alla data di inizio"))
        
        return value


class ValidationMixin:
    """Mixin per aggiungere validazione standardizzata ai form"""
    
    def add_validation_error(self, field_name, message):
        """Aggiunge un errore di validazione standardizzato"""
        if field_name in self.errors:
            self.errors[field_name].append(message)
        else:
            self.errors[field_name] = [message]
    
    def validate_required_fields(self, required_fields, cleaned_data):
        """Valida campi obbligatori"""
        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                self.add_validation_error(field_name, _("Questo campo è obbligatorio"))
    
    def validate_conditional_fields(self, conditions, cleaned_data):
        """Valida campi condizionali"""
        for condition in conditions:
            field_name = condition['field']
            condition_field = condition['condition_field']
            condition_value = condition['condition_value']
            
            if cleaned_data.get(condition_field) == condition_value:
                if not cleaned_data.get(field_name):
                    self.add_validation_error(field_name, _("Questo campo è obbligatorio"))


class APIValidationMixin:
    """Mixin per validazione API standardizzata"""
    
    def get_validation_errors(self):
        """Restituisce errori di validazione in formato API standard"""
        if not hasattr(self, 'errors'):
            return {}
        
        return {
            'validation_errors': dict(self.errors),
            'error_count': sum(len(errors) for errors in self.errors.values())
        }
    
    def is_valid_for_api(self):
        """Verifica validità per API con gestione errori standardizzata"""
        is_valid = self.is_valid()
        if not is_valid:
            logger.warning(f"API validation failed: {self.get_validation_errors()}")
        return is_valid


# Validatori predefiniti per uso comune
POD_VALIDATOR = PODCodeValidator()
POWER_VALIDATOR = PowerValidator(min_value=0, max_value=1000)  # Max 1MW
EMAIL_UNIQUE_VALIDATOR = EmailUniquenessValidator()
USERNAME_UNIQUE_VALIDATOR = UsernameUniquenessValidator()
PDF_VALIDATOR = FileTypeValidator(allowed_extensions=['.pdf'], max_size_mb=10)
IMAGE_VALIDATOR = FileTypeValidator(allowed_extensions=['.jpg', '.jpeg', '.png'], max_size_mb=5)
