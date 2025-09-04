-- Script di inizializzazione database PostgreSQL per CerCollettiva
-- Questo script viene eseguito automaticamente al primo avvio del container PostgreSQL

-- Crea database se non esiste
SELECT 'CREATE DATABASE cercollettiva'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cercollettiva')\gexec

-- Crea utente se non esiste
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'cercollettiva_user') THEN

      CREATE ROLE cercollettiva_user LOGIN PASSWORD 'cercollettiva_pass';
   END IF;
END
$do$;

-- Concedi privilegi
GRANT ALL PRIVILEGES ON DATABASE cercollettiva TO cercollettiva_user;

-- Connessione al database cercollettiva
\c cercollettiva;

-- Concedi privilegi su schema public
GRANT ALL ON SCHEMA public TO cercollettiva_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cercollettiva_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cercollettiva_user;

-- Configurazioni per performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Estensioni utili
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Configurazioni per sicurezza
ALTER SYSTEM SET password_encryption = 'scram-sha-256';
ALTER SYSTEM SET ssl = on;

-- Log di inizializzazione
INSERT INTO pg_stat_statements_info VALUES (now(), 'Database initialized for CerCollettiva');
