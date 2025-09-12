# documents/views.py
import logging
import os
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.edit import DeleteView

from core.main_models import Plant
from core.validators import (
    IMAGE_VALIDATOR,
    PDF_VALIDATOR,
    APIValidationMixin,
    FileTypeValidator,
    ValidationMixin,
)

from .forms import DocumentUploadForm
from .models import Document, DocumentAccess

# import os
# import magic




logger = logging.getLogger(__name__)


def validate_file_upload_security(file):
    """Valida il file caricato per tipo, dimensione e nome - funzione riutilizzabile"""
    # Costanti di validazione
    ALLOWED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "txt"]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_FILENAME_LENGTH = 255

    # Validazione dimensione
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File troppo grande. Dimensione massima: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )

    # Validazione estensione
    ext = os.path.splitext(file.name)[1].lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Tipo di file non consentito. Tipi consentiti: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validazione nome file
    if len(file.name) > MAX_FILENAME_LENGTH:
        raise ValidationError(
            f"Nome file troppo lungo. Massimo {MAX_FILENAME_LENGTH} caratteri"
        )

    # Validazione caratteri speciali nel nome
    if not re.match(r"^[a-zA-Z0-9._-]+$", file.name):
        raise ValidationError(
            "Il nome del file contiene caratteri non validi. Utilizzare solo lettere, numeri, punti, trattini e underscore"
        )

    # Validazione nome file pericoloso
    dangerous_patterns = ["..", "/", "\\", "<script", "javascript:", "data:"]
    for pattern in dangerous_patterns:
        if pattern in file.name.lower():
            raise ValidationError("Nome file non sicuro rilevato")

    return True


class APIResponseHelper(ValidationMixin, APIValidationMixin):
    """Helper class for standardized API responses"""

    @staticmethod
    def success_response(data, status=200):
        """Return standardized success response"""
        return JsonResponse(
            {
                "status": "success",
                "data": data,
                "timestamp": timezone.now().isoformat(),
            },
            status=status,
        )

    @staticmethod
    def error_response(message, detail=None, status=400):
        """Return standardized error response"""
        response_data = {
            "status": "error",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
        if detail:
            response_data["detail"] = detail
        return JsonResponse(response_data, status=status)

    @staticmethod
    def validation_error_response(errors, status=400):
        """Return standardized validation error response"""
        return JsonResponse(
            {
                "status": "error",
                "message": "Validation failed",
                "validation_errors": errors,
                "timestamp": timezone.now().isoformat(),
            },
            status=status,
        )


class DocumentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Document
    template_name = "documents/document_confirm_delete.html"

    def test_func(self):
        document = self.get_object()
        return self.request.user == document.uploaded_by

    def get_success_url(self):
        # Se la richiesta proviene dalla pagina del profilo, torna al profilo
        referer = self.request.META.get("HTTP_REFERER", "")
        if "/users/profile/" in referer:
            return reverse_lazy("users:profile")
        return reverse_lazy("documents:list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Il documento è stato eliminato con successo.")
        return super().delete(request, *args, **kwargs)

    def handle_no_permission(self):
        messages.error(
            self.request, "Non hai i permessi per eliminare questo documento."
        )
        return redirect("documents:list")


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/list.html"
    context_object_name = "documents"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = self.get_queryset()

        # Inizializza il dizionario document_groups
        context["document_groups"] = {
            "identity": documents.filter(type="ID_DOC"),
            "technical": documents.filter(
                type__in=["SYSTEM_CERT", "PANELS_PHOTO", "INVERTER_PHOTO"]
            ),
            "administrative": documents.filter(type__in=["BILL", "GSE_DOC"]),
            "other": documents.filter(type="OTHER"),
            "gaudi": documents.filter(type="GAUDI"),  # Aggiunto qui il gruppo gaudi
        }

        # Documenti in scadenza
        context["expiring_documents"] = documents.filter(
            retention_date__lte=timezone.now().date() + timezone.timedelta(days=30)
        )

        # Documenti con dati personali
        if self.request.user.has_perm("documents.view_personal_data"):
            context["personal_documents"] = documents.filter(
                Q(type__in=["ID_DOC", "BILL"]) | Q(data_classification="PERSONAL")
            )

        # Plant context se arriva dalla vista di un impianto
        plant_id = self.request.GET.get("plant")
        if plant_id:
            context["plant"] = get_object_or_404(Plant, pk=plant_id)

        return context

    def get_queryset(self):
        base_queryset = Document.objects.filter(
            uploaded_by=self.request.user
        ).select_related("plant")

        # Filtra per impianto se specificato
        plant_id = self.request.GET.get("plant")
        if plant_id:
            base_queryset = base_queryset.filter(plant_id=plant_id)

        # Filtra documenti confidenziali se l'utente non ha i permessi
        if not self.request.user.has_perm("documents.view_confidential"):
            base_queryset = base_queryset.exclude(data_classification="CONFIDENTIAL")

        return base_queryset


class DocumentUploadView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = "documents/upload.html"

    def dispatch(self, request, *args, **kwargs):
        # Ottieni l'impianto dal parametro URL
        self.plant = get_object_or_404(Plant, pk=self.kwargs.get("plant_id"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["plant"] = self.plant
        return context

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        form.instance.source = "USER"
        form.instance.plant = self.plant

        # Imposta automaticamente la classificazione per documenti con dati personali
        if form.instance.type in ["ID_DOC", "BILL"]:
            form.instance.data_classification = "PERSONAL"

        response = super().form_valid(form)
        messages.success(self.request, "Documento caricato con successo.")
        return response

    def get_success_url(self):
        # Ritorna alla pagina dell'impianto dopo il caricamento
        return reverse_lazy("core:plant_detail", kwargs={"pk": self.plant.pk})


class DocumentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Document
    template_name = "documents/detail.html"
    context_object_name = "document"

    def test_func(self):
        document = self.get_object()
        user = self.request.user

        # Verifica permessi base
        if document.uploaded_by != user and not user.is_staff:
            return False

        # Verifica permessi speciali
        if document.data_classification == "CONFIDENTIAL":
            return user.has_perm("documents.view_confidential")
        if document.contains_personal_data:
            return user.has_perm("documents.view_personal_data")

        return True

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Registra l'accesso
        DocumentAccess.objects.create(
            document=obj,
            accessed_by=self.request.user,
            access_ip=self.request.META.get("REMOTE_ADDR"),
        )
        return obj


class GaudiUploadView(DocumentUploadView):
    """View specializzata per il caricamento degli attestati Gaudì"""

    template_name = "documents/gaudi_upload.html"

    def form_valid(self, form):
        form.instance.type = "GAUDI"
        form.instance.data_classification = "CONFIDENTIAL"
        return super().form_valid(form)

    def form_invalid(self, form):
        return APIResponseHelper.validation_error_response(form.errors)


class GaudiDetailView(DocumentDetailView):
    """View specializzata per i dettagli degli attestati Gaudì"""

    template_name = "documents/gaudi_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()

        # Aggiungi dati specifici Gaudì
        if document.plant and document.plant.gaudi_verified:
            context["gaudi_data"] = {
                "request_code": document.plant.gaudi_request_code,
                "censimp_code": document.plant.censimp_code,
                "validation_date": document.plant.validation_date,
                "nominal_power": document.plant.nominal_power,
                "expected_production": document.plant.expected_yearly_production,
            }

        return context


@require_POST
@login_required
def process_gaudi_attestation(request, pk):
    """
    Endpoint per elaborare manualmente un attestato Gaudì
    Utile in caso di errori nell'elaborazione automatica
    """
    document = get_object_or_404(Document, pk=pk, type="GAUDI")

    # Verifica permessi
    if not request.user.is_staff and document.plant.owner != request.user:
        return APIResponseHelper.error_response(
            "Non hai i permessi per elaborare questo documento", status=403
        )

    try:
        success = document.process_gaudi_attestation()
        if success:
            messages.success(request, "Attestato Gaudì elaborato con successo")
            return APIResponseHelper.success_response({"processed": True})
        else:
            return APIResponseHelper.error_response(
                "Elaborazione fallita", document.processing_errors, status=400
            )

    except Exception as e:
        logger.error(f"Error processing GAUDI attestation {pk}: {str(e)}")
        return APIResponseHelper.error_response(
            "Errore interno durante l'elaborazione",
            str(e) if settings.DEBUG else None,
            status=500,
        )


@login_required
def upload_gaudi_attestation(request, plant_id):
    """View per caricare un attestato Gaudì"""
    logger.info("=== Inizio Upload Attestato Gaudì ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content Type: {request.content_type}")
    logger.info(f"Files disponibili: {list(request.FILES.keys())}")
    logger.info(f"POST data disponibile: {list(request.POST.keys())}")

    if request.method != "POST":
        logger.warning("Metodo non consentito")
        return APIResponseHelper.error_response("Metodo non consentito", status=405)

    if "attestation" not in request.FILES:
        logger.warning("File attestation non trovato nella richiesta")
        logger.warning(f"Files ricevuti: {request.FILES}")
        return APIResponseHelper.error_response("Nessun file caricato", status=400)

    try:
        file = request.FILES["attestation"]
        logger.info(
            f"File ricevuto: {file.name} ({file.content_type}, {file.size} bytes)"
        )

        # Validate file using comprehensive validator
        try:
            validate_file_upload_security(file)
        except ValidationError as e:
            return APIResponseHelper.validation_error_response(
                {"attestation": [str(e)]}
            )

        plant = get_object_or_404(Plant, id=plant_id)

        if not request.user.is_staff and plant.owner != request.user:
            return APIResponseHelper.error_response(
                "Non hai i permessi per questo impianto", status=403
            )

        document = Document.objects.create(
            type="GAUDI",
            file=file,
            plant=plant,
            uploaded_by=request.user,
            source="USER",
            notes=request.POST.get("notes", ""),
            gdpr_consent=request.POST.get("gdpr_consent") == "on",
        )

        logger.info(f"Documento creato con successo (ID: {document.id})")

        return APIResponseHelper.success_response(
            {"document_id": document.id, "message": "Attestato caricato con successo"}
        )

    except Exception as e:
        logger.error(f"Errore durante l'upload: {str(e)}")
        return APIResponseHelper.error_response(
            "Errore durante l'upload", str(e) if settings.DEBUG else None, status=500
        )


@login_required
def gaudi_processing_status(request, pk):
    """Endpoint per verificare lo stato di elaborazione"""
    document = get_object_or_404(Document, pk=pk, type="GAUDI")

    # Verifica permessi
    if not request.user.is_staff and document.plant.owner != request.user:
        return APIResponseHelper.error_response(
            _("Non hai i permessi per questo documento"), status=403
        )

    response_data = {
        "status": document.processing_status,
        "errors": (
            document.processing_errors
            if document.processing_status == "FAILED"
            else None
        ),
        "processed_at": (
            document.processed_at.isoformat() if document.processed_at else None
        ),
    }

    return APIResponseHelper.success_response(response_data)


@login_required
def gaudi_attestation_details(request, pk):
    """View per visualizzare i dettagli di un attestato Gaudì"""
    document = get_object_or_404(Document, pk=pk, type="GAUDI")

    # Verifica permessi
    if not request.user.is_staff and document.plant.owner != request.user:
        return APIResponseHelper.error_response(
            _("Non hai i permessi per questo documento"), status=403
        )

    # Registra l'accesso al documento
    document.record_access(request.user)

    response_data = {
        "document": {
            "id": document.id,
            "uploaded_at": document.uploaded_at.isoformat(),
            "uploaded_by": document.uploaded_by.get_full_name()
            or document.uploaded_by.username,
            "plant": {
                "id": document.plant.id,
                "name": document.plant.name,
                "pod_code": document.plant.pod_code,
            },
            "gaudi_data": (
                {
                    "request_code": document.plant.gaudi_request_code,
                    "censimp_code": document.plant.censimp_code,
                    "validation_date": (
                        document.plant.validation_date.isoformat()
                        if document.plant.validation_date
                        else None
                    ),
                    "verified": document.plant.gaudi_verified,
                }
                if document.plant
                else None
            ),
        }
    }

    return APIResponseHelper.success_response(response_data)
