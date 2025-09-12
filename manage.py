# manage.py
#!/usr/bin/env python
import os
import sys

from dotenv import load_dotenv


def main():
    """Run administrative tasks."""
    # Carica le variabili d'ambiente dal file .env
    load_dotenv()

    # Usa il valore da .env o default a 'local'
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cercollettiva.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
