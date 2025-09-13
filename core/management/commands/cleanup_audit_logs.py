# core/management/commands/cleanup_audit_logs.py
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.signals.audit import cleanup_expired_audit_logs

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Pulisce i log di audit scaduti per mantenere il database ottimizzato"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra cosa verrebbe eliminato senza effettuare la pulizia",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Output dettagliato",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        # verbose = options["verbose"]  # Unused variable

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN - Nessuna modifica verrà effettuata")
            )
            self._show_expired_logs()
        else:
            self.stdout.write("Inizio pulizia audit logs...")
            try:
                cleanup_expired_audit_logs()
                self.stdout.write(
                    self.style.SUCCESS("Pulizia audit logs completata con successo")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Errore durante la pulizia: {e}"))
                logger.error(f"Errore comando cleanup_audit_logs: {e}")

    def _show_expired_logs(self):
        """Mostra i log che verrebbero eliminati"""
        from core.models.audit import (
            CERDocumentAudit,
            EconomicTransactionAudit,
            UserActionAudit,
        )

        now = timezone.now()

        # Audit transazioni economiche
        expired_economic = EconomicTransactionAudit.objects.filter(
            retention_date__lt=now
        )
        self.stdout.write(
            f"Audit transazioni economiche scadute: {expired_economic.count()}"
        )

        # Audit documenti CER
        expired_docs = CERDocumentAudit.objects.filter(retention_date__lt=now)
        self.stdout.write(f"Audit documenti CER scaduti: {expired_docs.count()}")

        # Audit azioni utente
        expired_actions = UserActionAudit.objects.filter(retention_date__lt=now)
        self.stdout.write(f"Audit azioni utente scadute: {expired_actions.count()}")

        total = (
            expired_economic.count() + expired_docs.count() + expired_actions.count()
        )
        self.stdout.write(f"Totale record da eliminare: {total}")
