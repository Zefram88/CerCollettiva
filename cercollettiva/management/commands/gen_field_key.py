from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a valid FIELD_ENCRYPTION_KEY (Fernet base64 url-safe 32 bytes)"

    def handle(self, *args, **options):
        try:
            from cryptography.fernet import Fernet

            key = Fernet.generate_key().decode("utf-8")
            self.stdout.write(self.style.SUCCESS(key))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to generate key: {e}"))

