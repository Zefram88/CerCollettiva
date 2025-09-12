# documents/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os
import re
from .models import Document
from core.validators import FileTypeValidator

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['type', 'file', 'notes', 'data_classification', 'gdpr_consent']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type'].widget.attrs.update({'class': 'form-select'})
        
        # Rendi il consenso GDPR obbligatorio per documenti con dati personali
        self.fields['gdpr_consent'].required = False
        
        # Aggiungi help text dinamico per il consenso GDPR
        self.fields['gdpr_consent'].help_text = """
            Confermo di aver letto l'informativa sulla privacy e acconsento al trattamento 
            dei dati personali contenuti in questo documento. I dati saranno utilizzati 
            esclusivamente per le finalità relative alla gestione della comunità energetica 
            e conservati secondo i termini di legge.
        """

    def clean(self):
        cleaned_data = super().clean()
        doc_type = cleaned_data.get('type')
        gdpr_consent = cleaned_data.get('gdpr_consent')
        data_classification = cleaned_data.get('data_classification')

        # Verifica consenso GDPR per documenti con dati personali
        if doc_type in ['ID_DOC', 'BILL'] or data_classification == 'PERSONAL':
            if not gdpr_consent:
                raise forms.ValidationError(
                    "Il consenso al trattamento dei dati è obbligatorio per questo tipo di documento"
                )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validazione completa del file
            self._validate_file_upload(file)
        return file
    
    def _validate_file_upload(self, file):
        """Valida il file caricato per tipo, dimensione e nome"""
        # Costanti di validazione
        ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt']
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        MAX_FILENAME_LENGTH = 255
        
        # Validazione dimensione
        if file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(
                _("File troppo grande. Dimensione massima: {size:.1f}MB").format(
                    size=MAX_FILE_SIZE / (1024*1024)
                )
            )
        
        # Validazione estensione
        ext = os.path.splitext(file.name)[1].lower().lstrip('.')
        if ext not in ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                _("Tipo di file non consentito. Tipi consentiti: {types}").format(
                    types=', '.join(ALLOWED_EXTENSIONS)
                )
            )
        
        # Validazione nome file
        if len(file.name) > MAX_FILENAME_LENGTH:
            raise forms.ValidationError(
                _("Nome file troppo lungo. Massimo {max} caratteri").format(
                    max=MAX_FILENAME_LENGTH
                )
            )
        
        # Validazione caratteri speciali nel nome
        if not re.match(r'^[a-zA-Z0-9._-]+$', file.name):
            raise forms.ValidationError(
                _("Il nome del file contiene caratteri non validi. Utilizzare solo lettere, numeri, punti, trattini e underscore")
            )
        
        # Validazione nome file pericoloso
        dangerous_patterns = ['..', '/', '\\', '<script', 'javascript:', 'data:']
        for pattern in dangerous_patterns:
            if pattern in file.name.lower():
                raise forms.ValidationError(
                    _("Nome file non sicuro rilevato")
                )
        
        return True