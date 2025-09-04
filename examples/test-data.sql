-- Dati di test per CerCollettiva
-- Questo file viene caricato automaticamente nel database di sviluppo

-- Inserisci dati di test solo se il database è vuoto
DO $$
BEGIN
    -- Verifica se ci sono già dati
    IF NOT EXISTS (SELECT 1 FROM django_migrations LIMIT 1) THEN
        -- Dati di test verranno inseriti qui dopo le migrazioni Django
        -- Questo file serve come placeholder per dati di test futuri
        RAISE NOTICE 'Test data placeholder - Django migrations will populate the database';
    END IF;
END $$;
