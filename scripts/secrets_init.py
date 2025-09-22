import os
import secrets
import shutil
from cryptography.fernet import Fernet

SECRETS_PATH = '/secrets'
TEMP_PATH = '/tmp/secrets'

def ensure_secrets_directory():
    """Assicura che la directory secrets esista e sia scrivibile"""
    if not os.path.exists(SECRETS_PATH):
        os.makedirs(SECRETS_PATH, mode=0o755)
    
    # Crea directory temporanea con permessi corretti
    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH, mode=0o755)
    
    # Prova a scrivere un file di test
    test_file = os.path.join(TEMP_PATH, 'test_write')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"Directory {TEMP_PATH} è scrivibile")
        return True
    except Exception as e:
        print(f"Directory {TEMP_PATH} non è scrivibile: {e}")
        return False

def generate_secret_key(path):
    key_file = os.path.join(path, 'django_secret_key')
    if not os.path.exists(key_file):
        print("Generazione di una nuova SECRET_KEY per Django...")
        secret_key = secrets.token_urlsafe(50)
        # Crea file temporaneo
        temp_file = os.path.join(TEMP_PATH, 'django_secret_key')
        with open(temp_file, 'w') as f:
            f.write(secret_key)
        os.chmod(temp_file, 0o644)
        # Copia nel volume secrets usando sudo
        import subprocess
        try:
            subprocess.run(['sudo', 'cp', temp_file, key_file], check=True)
            subprocess.run(['sudo', 'chmod', '644', key_file], check=True)
            subprocess.run(['sudo', 'chown', 'cercollettiva:cercollettiva', key_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Errore nel copiare {temp_file} a {key_file}: {e}")
            # Fallback: prova a copiare direttamente
            shutil.copy2(temp_file, key_file)
        os.remove(temp_file)
        print("SECRET_KEY generata e salvata.")

def generate_encryption_key(path):
    key_file = os.path.join(path, 'field_encryption_key')
    if not os.path.exists(key_file):
        print("Generazione di una nuova FIELD_ENCRYPTION_KEY...")
        encryption_key = Fernet.generate_key().decode()
        # Crea file temporaneo
        temp_file = os.path.join(TEMP_PATH, 'field_encryption_key')
        with open(temp_file, 'w') as f:
            f.write(encryption_key)
        os.chmod(temp_file, 0o644)
        # Copia nel volume secrets usando sudo
        import subprocess
        try:
            subprocess.run(['sudo', 'cp', temp_file, key_file], check=True)
            subprocess.run(['sudo', 'chmod', '644', key_file], check=True)
            subprocess.run(['sudo', 'chown', 'cercollettiva:cercollettiva', key_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Errore nel copiare {temp_file} a {key_file}: {e}")
            # Fallback: prova a copiare direttamente
            shutil.copy2(temp_file, key_file)
        os.remove(temp_file)
        print("FIELD_ENCRYPTION_KEY generata e salvata.")
        # Verifica che la chiave sia valida
        try:
            Fernet(encryption_key.encode())
            print("✓ Chiave FIELD_ENCRYPTION_KEY valida")
        except Exception as e:
            print(f"✗ Chiave FIELD_ENCRYPTION_KEY non valida: {e}")

def generate_password(name, path):
    pass_file = os.path.join(path, f"{name}_password")
    if not os.path.exists(pass_file):
        print(f"Generazione di una nuova password per {name}...")
        password = secrets.token_urlsafe(32)
        # Crea file temporaneo
        temp_file = os.path.join(TEMP_PATH, f"{name}_password")
        with open(temp_file, 'w') as f:
            f.write(password)
        os.chmod(temp_file, 0o644)
        # Copia nel volume secrets usando sudo
        import subprocess
        try:
            subprocess.run(['sudo', 'cp', temp_file, pass_file], check=True)
            subprocess.run(['sudo', 'chmod', '644', pass_file], check=True)
            subprocess.run(['sudo', 'chown', 'cercollettiva:cercollettiva', pass_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Errore nel copiare {temp_file} a {pass_file}: {e}")
            # Fallback: prova a copiare direttamente
            shutil.copy2(temp_file, pass_file)
        os.remove(temp_file)
        print(f"Password per {name} generata e salvata.")

if __name__ == '__main__':
    if not ensure_secrets_directory():
        print("Errore: impossibile creare directory temporanea")
        exit(1)
    
    generate_secret_key(SECRETS_PATH)
    generate_encryption_key(SECRETS_PATH)
    generate_password('redis', SECRETS_PATH)
    generate_password('mqtt', SECRETS_PATH)
    print("Inizializzazione dei segreti completata.")


