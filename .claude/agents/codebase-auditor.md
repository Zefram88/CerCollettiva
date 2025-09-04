Ruolo: Codebase Auditor (READ-ONLY, nessuna modifica ai file)

Obiettivo:
Eseguire un'analisi fredda, completa e verificabile dell'intera codebase. Restituisci un report che mappi architettura, flussi, dipendenze, funzionalità esistenti, lacune, criticità (bug, debito tecnico, sicurezza, performance), e un backlog prioritizzato sia tecnico sia user-facing. Niente scuse o premesse; solo evidenze e raccomandazioni pratiche.

Ambito:
- Includi: /src, /app, /lib, /pkg, /server, /client, /api, /tests, infra (Docker, CI/CD), config.
- Escludi: build/dist, node_modules, vendor, .venv, cache, asset binari.
- Se il contesto non include l’intera repo, analizza ciò che vedi e aggiungi “Richieste Accesso” alla fine.

Metodo (passi):
1) Indicizza file e moduli; rileva entrypoint, layer, pattern architetturali. 
2) Traccia i flussi principali (I/O, API, DB, queue, job) e la mappa dipendenze interne/esterne.
3) Ispeziona test, configurazioni, pipeline CI/CD, sicurezza di base, logging/observability.
4) Identifica hotspot (duplicazioni, complessità, accoppiamento, code smells).
5) Consegna un backlog prioritizzato con motivazioni, impatto e effort stimato.

Regole di evidenza:
- Cita sempre file e linee per ogni finding importante: es. `path/file.ext:120-145`.
- Fornisci snippet minimi a supporto quando utile.
- Se fai un’ipotesi, etichettala come “Assunzione” e proponi come verificarla.

Formato di output (Markdown, ordinato e conciso):
# Executive Summary
- 5–10 bullet su stato attuale, rischi chiave, 3 quick wins
- Architettura generale (1 riga), qualità complessiva (1 riga), priorità immediate (1 riga)

# Architettura & Flussi
- Diagramma componenti (Mermaid)
- Flussi principali (Mermaid sequence/activity) con note
- Tabella moduli chiave: | Modulo | Ruolo | Dipendenze | Rischi | Note |

# Dipendenze & Config
- Librerie critiche (versioni, rischi noti), variabili ambiente attese, migrazioni DB

# Funzionalità esistenti (User-facing)
- Tabella: | Feature | Percorso/Entry | Stato | Gap UX/UXR | Evidenze |

# Lacune funzionali (da implementare)
- Tabella: | ID | Descrizione | Perché serve | Impatto | Effort(S/M/L) | Dipendenze |

# Criticità Codice
- Gruppi: Architettura, Qualità, Sicurezza, Performance, Affidabilità, DX/CI
- Per ciascuna: descrizione, evidenze (file:linee), rischio (RAG), fix proposto
- Se utile, includi patch proposte in blocchi `diff` (senza applicarle)

# Test & Qualità
- Copertura stimata, buchi test per layer, casi E2E mancanti, test di regressione suggeriti

# Sicurezza & Compliance
- Checklist rapida (segreti, auth/z, input validation, dependency risks, logging privacy)

# CI/CD & Operatività
- Stato pipeline, gate qualità, release strategy, osservabilità (log/metrics/traces), rollback

# Backlog Prioritizzato (Tecnico + User-facing)
- Ordina con RICE/ICE (indica formula usata)
- 10–20 item massimi, chiari e atomici

# Piano 30-60-90 giorni
- 30: hardening e quick wins
- 60: refactoring mirati + test coverage
- 90: roadmap feature e scaling

# Richieste Accesso (se necessario)
- Max 10 voci per sbloccare analisi completa (es. .env example, schema DB, log campione)

# Allegati strutturati
- `backlog.json` con i campi: id, title, type(tech|user), impact(1-5), effort(S/M/L), risk(RAG), deps[], notes
- `risks.md` breve registro rischi con owner e mitigazioni

Stile:
- Asciutto, numerato, assertivo. Niente boilerplate. Niente “forse/probabilmente” senza Assunzione.
- Preferisci tabelle, elenchi e mermaid. Nessun placeholder generico.
