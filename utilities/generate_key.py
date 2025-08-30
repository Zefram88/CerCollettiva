# generate_key.py
from cryptography.fernet import Fernet

# Genera una chiave Fernet valida
key = Fernet.generate_key()
print(f"FIELD_ENCRYPTION_KEY = '{key.decode()}'")