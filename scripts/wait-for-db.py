#!/usr/bin/env python3
"""
Script per attendere che il database PostgreSQL sia pronto
Utilizzato durante il setup automatico Docker
"""

import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError

def wait_for_database():
    """Attende che il database PostgreSQL sia pronto"""
    max_retries = 30
    retry_count = 0
    
    # Configurazione database da variabili d'ambiente
    db_config = {
        'host': os.getenv('DB_HOST', 'db'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'cercollettiva_user'),
        'password': os.getenv('DB_PASSWORD', 'cercollettiva_pass'),
        'database': os.getenv('DB_NAME', 'cercollettiva')
    }
    
    print(f"Attesa database PostgreSQL su {db_config['host']}:{db_config['port']}...")
    
    while retry_count < max_retries:
        try:
            # Tentativo di connessione
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.close()
            conn.close()
            
            print("✓ Database PostgreSQL pronto")
            return True
            
        except OperationalError as e:
            retry_count += 1
            print(f"  Tentativo {retry_count}/{max_retries} - Database non pronto: {e}")
            
            if retry_count < max_retries:
                time.sleep(2)
            else:
                print("✗ Database non disponibile dopo 60 secondi")
                return False
    
    return False

def wait_for_redis():
    """Attende che Redis sia pronto (opzionale)"""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/1')
        r = redis.from_url(redis_url)
        r.ping()
        print("✓ Redis pronto")
        return True
    except Exception as e:
        print(f"⚠ Redis non disponibile: {e}")
        return False

def main():
    """Funzione principale"""
    print("Attesa dipendenze database...")
    
    # Attendi database principale
    if not wait_for_database():
        print("✗ Impossibile connettersi al database")
        sys.exit(1)
    
    # Attendi Redis (opzionale)
    wait_for_redis()
    
    print("✓ Tutte le dipendenze database sono pronte")
    return True

if __name__ == "__main__":
    main()
