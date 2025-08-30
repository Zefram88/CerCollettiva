# create_superuser.py
import os
import django
from django.db import transaction
from django.core.exceptions import ValidationError

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cercollettiva.settings.local")
django.setup()

def create_or_update_superuser(username, email, first_name, last_name, fiscal_code, password=None):
    try:
        # Get the user model
        User = django.contrib.auth.get_user_model()
        
        with transaction.atomic():
            # Preparazione dei dati utente
            user_data = {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'legal_type': 'PRIVATE',
                'profit_type': 'NON_PROFIT',
                'fiscal_code': fiscal_code,
                'phone': '0000000000',
                'address': 'Indirizzo temporaneo',
                'is_staff': True,
                'is_superuser': True,
            }

            try:
                # Prova a recuperare l'utente esistente
                user = User.objects.get(username=username)
                print(f"Aggiornamento utente esistente: {username}")
                
                # Aggiorna i campi
                for key, value in user_data.items():
                    setattr(user, key, value)
                
            except User.DoesNotExist:
                # Crea nuovo utente
                print(f"Creazione nuovo superuser: {username}")
                user = User.objects.create_superuser(
                    password=password,
                    **user_data
                )
            
            # Valida prima di salvare
            try:
                user.full_clean()
            except ValidationError as e:
                print("Errori di validazione:")
                for field, errors in e.message_dict.items():
                    print(f"- {field}: {', '.join(errors)}")
                raise
            
            # Salva le modifiche
            user.save()
            
            print(f"Superuser {username} creato/aggiornato con successo!")
            print(f"Nome completo: {user.get_full_name()}")
            return True
            
    except Exception as e:
        print(f"Errore durante la creazione/aggiornamento del superuser: {e}")
        return False

if __name__ == "__main__":
    # Configura questi valori con i tuoi dati reali
    superuser_data = {
        'username': 'atomozero',
        'email': 'atomozero@proton.me',
        'first_name': 'Andrea',
        'last_name': 'Bernardi',
        'fiscal_code': 'BRNNDR80T30L736D',  # Inserisci un codice fiscale valido
        'password': 'tuapassword123'  # Cambia questa password!
    }
    
    success = create_or_update_superuser(**superuser_data)
    
    if success:
        print("\nOperazione completata con successo!")
        print("Ricordati di:")
        print("1. Accedere al pannello di amministrazione")
        print("2. Aggiornare i campi temporanei (telefono, indirizzo)")
        print("3. Verificare che tutti i permessi siano corretti")
    else:
        print("\nSi è verificato un errore durante l'operazione.")
        print("Controlla i messaggi di errore sopra per maggiori dettagli.")