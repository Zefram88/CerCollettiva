# Sistema di Monitoring CerCollettiva

## Panoramica

CerCollettiva include un sistema di monitoring completo che raccoglie dati in tempo reale su performance, dispositivi, accessibilità, feedback utenti e A/B testing. Il sistema è progettato per fornire insights dettagliati sull'esperienza utente e le performance dell'applicazione.

## Architettura

### Componenti

1. **Client-Side Monitoring Scripts**
   - `performance-monitor.js` - Core Web Vitals e metriche performance
   - `device-detector.js` - Rilevamento dispositivo e browser
   - `accessibility-audit.js` - Audit accessibilità automatico
   - `user-feedback.js` - Sistema feedback utenti
   - `ab-testing.js` - Framework A/B testing
   - `analytics-dashboard.js` - Dashboard analytics in-browser

2. **Server-Side API Endpoints**
   - `/api/performance-metrics/` - Raccolta metriche performance
   - `/api/device-info/` - Informazioni dispositivo
   - `/api/accessibility-audit/` - Risultati audit accessibilità
   - `/api/user-feedback/` - Feedback utenti
   - `/api/session-data/` - Dati sessione utente
   - `/api/ab-testing/event/` - Eventi A/B testing
   - `/api/ab-testing/participation/` - Partecipazioni A/B testing

3. **Database Models**
   - `PerformanceMetrics` - Core Web Vitals e memory usage
   - `DeviceInfo` - Informazioni dispositivo e browser
   - `AccessibilityAudit` - Risultati audit accessibilità
   - `UserFeedback` - Feedback e rating utenti
   - `SessionData` - Dati sessione e interazioni
   - `ABTestingParticipation` - Partecipazioni test A/B
   - `ABTestingEvent` - Eventi A/B testing

## Metriche Raccolte

### Performance Metrics

- **Core Web Vitals**
  - LCP (Largest Contentful Paint)
  - FID (First Input Delay)
  - CLS (Cumulative Layout Shift)
  - FCP (First Contentful Paint)
  - TTFB (Time to First Byte)

- **Memory Usage**
  - Memoria utilizzata
  - Memoria totale disponibile
  - Limite memoria

- **Animation Performance**
  - Frame rate animazioni
  - Tempo risposta eventi
  - Errori JavaScript

### Device Information

- **Dispositivo**
  - Tipo (desktop, mobile, tablet)
  - Sistema operativo e versione
  - Browser e versione

- **Schermo**
  - Risoluzione schermo
  - Dimensioni viewport
  - Pixel ratio

- **Capacità**
  - Supporto touch
  - Accelerazione hardware
  - Supporto WebGL
  - Tipo connessione
  - Memoria dispositivo

### Accessibility Audit

- **Score Accessibilità**
  - Punteggio complessivo (0-100)
  - Numero errori
  - Numero warning

- **Issues Rilevate**
  - Elementi non focusabili
  - Contrasto colori
  - Testo alternativo immagini
  - Struttura heading
  - Etichette form
  - Attributi ARIA

### User Feedback

- **Rating**
  - Rating complessivo (1-5)
  - Rating performance
  - Commenti e suggerimenti

- **Session Data**
  - Durata sessione
  - Tempo su pagina
  - Numero interazioni
  - Problemi riportati

### A/B Testing

- **Esperimenti Attivi**
  - Button style (default, rounded, shadow)
  - Card layout (default, compact, expanded)
  - Color scheme (light, dark, auto)

- **Metriche Tracciate**
  - Click rate
  - Conversion rate
  - Engagement time
  - Scroll depth

## Dashboard Analytics

### Accesso Dashboard

La dashboard analytics è accessibile tramite:
- **Tastiera**: `Ctrl+Shift+A`
- **Browser**: Solo in modalità sviluppo

### Metriche Visualizzate

- **Performance Overview**
  - Core Web Vitals in tempo reale
  - Memory usage trends
  - Error rate

- **Device Analytics**
  - Distribuzione dispositivi
  - Browser usage
  - Screen resolutions

- **User Experience**
  - Session duration
  - Page views
  - User feedback scores

- **A/B Testing Results**
  - Conversion rates per variant
  - Statistical significance
  - Performance impact

## Configurazione

### Client-Side

I script di monitoring sono automaticamente caricati in tutte le pagine tramite `base.html`:

```html
<script src="{% static 'js/performance-monitor.js' %}"></script>
<script src="{% static 'js/device-detector.js' %}"></script>
<script src="{% static 'js/accessibility-audit.js' %}"></script>
<script src="{% static 'js/user-feedback.js' %}"></script>
<script src="{% static 'js/ab-testing.js' %}"></script>
<script src="{% static 'js/analytics-dashboard.js' %}"></script>
```

### Server-Side

Gli endpoint API sono configurati in `core/urls_monitoring.py` e inclusi nel main `cercollettiva/urls.py`.

### Database

I modelli di monitoring sono definiti in `core/models.py` e le migrazioni sono applicate automaticamente.

## Privacy e GDPR

### Dati Raccolti

Il sistema raccoglie solo dati tecnici necessari per:
- Migliorare le performance dell'applicazione
- Ottimizzare l'esperienza utente
- Condurre test A/B per miglioramenti

### Consenso

- I dati di performance e dispositivo sono raccolti automaticamente
- Il feedback utenti richiede consenso esplicito
- I dati A/B testing sono anonimizzati

### Retention

- Dati performance: 90 giorni
- Dati sessione: 30 giorni
- Feedback utenti: 1 anno
- Dati A/B testing: 6 mesi

## Troubleshooting

### Problemi Comuni

1. **Dashboard non si apre**
   - Verificare che il server sia in modalità sviluppo
   - Controllare console browser per errori JavaScript

2. **Dati non salvati**
   - Verificare connessione database
   - Controllare logs server per errori API

3. **Performance impact**
   - I script sono ottimizzati per minimo impatto
   - Monitoring avviene in background
   - Dati inviati in batch per ridurre richieste

### Logs

- **Client-side**: Console browser
- **Server-side**: `logs/cercollettiva.log`
- **API errors**: Logs Django standard

## Sviluppo

### Aggiungere Nuove Metriche

1. Aggiornare modello database
2. Modificare API endpoint
3. Aggiornare client-side script
4. Aggiornare dashboard

### A/B Testing

Per aggiungere nuovi esperimenti:

1. Definire experiment in `ab-testing.js`
2. Implementare variants nel CSS/HTML
3. Tracciare metriche rilevanti
4. Analizzare risultati

## Roadmap

### Prossime Funzionalità

- [ ] Real-time notifications per performance issues
- [ ] Automated alerts per accessibility problems
- [ ] Advanced A/B testing con machine learning
- [ ] Integration con external analytics tools
- [ ] Mobile app monitoring
- [ ] Performance budgets e monitoring
- [ ] User journey tracking
- [ ] Conversion funnel analysis
