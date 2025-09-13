# Esempio Sistema di Progressione

## Scenario: Completamento Story e Passaggio Automatico

### 1. Stato Iniziale
```
EPIC attivo: EPIC-<id>-<titolo>
Story attiva: S001-<story-name>
Slice attivo: Slice <n>/<n> (ultimo)
```

### 2. Completamento Story
```
Utente: COMPLETE STORY

AI: ✅ S001-<story-name>.mdc → COMPLETED
✅ DoD validato: <n>/<n> criteri soddisfatti
✅ Checkpoint salvato: checkpoint-<timestamp>.mdc
✅ Progressione: S002-<next-story>.mdc → ACTIVE
✅ active/current-story.mdc aggiornato

📊 PROGRESSO EPIC
EPIC-<id>: <n>% completato (<n>/<n> Story)
Prossima Story: S002-<next-story> (READY)
```

### 3. Stato Dopo Completamento
```
active/current-epic.mdc → EPIC-<id>-<titolo>.mdc
active/current-story.mdc → S002-<next-story>.mdc
```

### 4. Continuazione Lavoro
```
Utente: STATUS

AI: 📊 STATO LAVORO ATTUALE
EPIC attivo: EPIC-<id>-<titolo>
Story attiva: S002-<story-name>
Slice attivo: Slice <n>/<n>

Progresso EPIC: <n>% (<n>/<n> Story completate)
Progresso Story: <n>% (<n>/<n> Slice completati)

Prossimi passi:
1. Iniziare Slice 1: <descrizione-slice> (<n> file, <n> LOC)
2. Continuare con Slice 2: <descrizione-slice>
3. Completare Slice 3: <descrizione-slice>
4. Finalizzare Slice 4: <descrizione-slice>

Checkpoint disponibili:
- checkpoint-<timestamp>.mdc (ultimo)
- checkpoint-<timestamp>.mdc
```

## Scenario: Passaggio Manuale

### 1. Passaggio Manuale a Story Successiva
```
Utente: NEXT STORY

AI: 📊 STATO ATTUALE
Story attiva: S002-<story-name> (IN_PROGRESS)
Slice completati: <n>/<n>
Prossima Story: S003-<next-story> (READY)

Confermi passaggio a S003? (y/n)

Utente: y

AI: ✅ Progressione: S003-<next-story>.mdc → ACTIVE
✅ active/current-story.mdc aggiornato
✅ Checkpoint salvato: checkpoint-<timestamp>.mdc
```

### 2. Passaggio Manuale a EPIC Successivo
```
Utente: NEXT EPIC

AI: 📊 STATO ATTUALE
EPIC attivo: EPIC-<id>-<titolo> (IN_PROGRESS)
Story completate: <n>/<n>
Prossimo EPIC: EPIC-<next-id>-<titolo> (READY)

Confermi passaggio a EPIC-<next-id>? (y/n)

Utente: y

AI: ✅ Progressione: EPIC-<next-id>-<titolo>.mdc → ACTIVE
✅ active/current-epic.mdc aggiornato
✅ active/current-story.mdc → S001-<prima-story>.mdc
✅ Checkpoint salvato: checkpoint-<timestamp>.mdc
```

## Meccanismi di Tracciamento

### File di Stato
- `active/current-epic.mdc` → Nome file EPIC attivo
- `active/current-story.mdc` → Nome file Story attiva
- `active/checkpoint-*.mdc` → Checkpoint temporali

### Aggiornamenti Automatici
1. **COMPLETE STORY**: Auto-progressione alla Story successiva
2. **COMPLETE EPIC**: Auto-progressione all'EPIC successivo
3. **Checkpoint**: Salvataggio automatico ad ogni transizione
4. **Links simbolici**: Aggiornamento automatico dei riferimenti

### Validazioni
- **DoD**: Verifica criteri di completamento prima del passaggio
- **Dipendenze**: Controllo dipendenze tra Story
- **Gate EPIC**: Validazione gate prima del completamento EPIC
- **Rollback**: Possibilità di tornare indietro con RESUME
