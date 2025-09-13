# documents/services.py
import hashlib

from django.core.files import File
from django.template.loader import render_to_string

import pdfkit

from .models import Document


class SystemDocumentService:
    @staticmethod
    def generate_cer_document(
        user, plant, document_type, context, classification="INTERNAL"
    ):
        """
        Genera un documento di sistema (es. contratto, report, ecc.)
        con gestione della classificazione e retention
        """
        # Genera il contenuto HTML dal template
        html_content = render_to_string(
            f"documents/system/{document_type}.html", context
        )

        # Converti HTML in PDF
        pdf_file = pdfkit.from_string(html_content, False)

        # Crea il documento nel sistema
        doc = Document.objects.create(
            type=document_type,
            source="SYSTEM",
            uploaded_by=user,
            plant=plant,
            data_classification=classification,
            notes=f"Documento generato automaticamente dal sistema - {document_type}",
            gdpr_consent=True,  # I documenti di sistema hanno il consenso implicito
        )

        # Genera nome file sicuro
        filename = (
            f"{document_type}_{plant.id}_{doc.uploaded_at.strftime('%Y%m%d')}.pdf"
        )

        # Salva il file e genera checksum
        doc.file.save(filename, File(open(pdf_file, "rb")))
        doc.generate_checksum()

        # Imposta retention date
        doc.set_retention_period()
        doc.save()

        return doc

    @staticmethod
    def generate_document_hash(file_path):
        """Genera hash SHA-256 per un file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
