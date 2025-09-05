/**
 * A/B Testing System - CerCollettiva
 * Sistema per testare diverse versioni dell'interfaccia
 */

class ABTestingSystem {
    constructor() {
        this.experiments = {};
        this.userId = this.generateUserId();
        this.init();
    }

    generateUserId() {
        let userId = localStorage.getItem('ab_testing_user_id');
        if (!userId) {
            userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('ab_testing_user_id', userId);
        }
        return userId;
    }

    init() {
        // Carica esperimenti attivi
        this.loadActiveExperiments();
        
        // Applica esperimenti
        this.applyExperiments();
        
        // Monitora risultati
        this.monitorResults();
    }

    loadActiveExperiments() {
        // Esperimenti attivi
        this.experiments = {
            'button_style': {
                name: 'Button Style Test',
                description: 'Testa diversi stili di bottoni',
                variants: ['default', 'rounded', 'shadow'],
                traffic: 0.5, // 50% degli utenti
                startDate: '2025-01-01',
                endDate: '2025-02-01',
                metrics: ['click_rate', 'conversion_rate']
            },
            'card_layout': {
                name: 'Card Layout Test',
                description: 'Testa diversi layout delle card',
                variants: ['default', 'compact', 'expanded'],
                traffic: 0.3, // 30% degli utenti
                startDate: '2025-01-01',
                endDate: '2025-02-01',
                metrics: ['engagement_time', 'scroll_depth']
            },
            'color_scheme': {
                name: 'Color Scheme Test',
                description: 'Testa diversi schemi di colori',
                variants: ['default', 'warm', 'cool'],
                traffic: 0.2, // 20% degli utenti
                startDate: '2025-01-01',
                endDate: '2025-02-01',
                metrics: ['user_satisfaction', 'bounce_rate']
            }
        };
    }

    applyExperiments() {
        Object.keys(this.experiments).forEach(experimentId => {
            const experiment = this.experiments[experimentId];
            
            // Verifica se l'utente è incluso nell'esperimento
            if (this.isUserInExperiment(experimentId, experiment)) {
                const variant = this.getUserVariant(experimentId, experiment);
                this.applyVariant(experimentId, variant);
                
                // Registra partecipazione
                this.recordParticipation(experimentId, variant);
            }
        });
    }

    isUserInExperiment(experimentId, experiment) {
        // Verifica date
        const now = new Date();
        const startDate = new Date(experiment.startDate);
        const endDate = new Date(experiment.endDate);
        
        if (now < startDate || now > endDate) {
            return false;
        }

        // Verifica traffic
        const userHash = this.hashUserId(experimentId);
        return userHash < experiment.traffic;
    }

    getUserVariant(experimentId, experiment) {
        const userHash = this.hashUserId(experimentId);
        const variantIndex = Math.floor(userHash * experiment.variants.length);
        return experiment.variants[variantIndex];
    }

    hashUserId(experimentId) {
        const str = this.userId + experimentId;
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash) / 2147483647; // Normalize to 0-1
    }

    applyVariant(experimentId, variant) {
        switch (experimentId) {
            case 'button_style':
                this.applyButtonStyleVariant(variant);
                break;
            case 'card_layout':
                this.applyCardLayoutVariant(variant);
                break;
            case 'color_scheme':
                this.applyColorSchemeVariant(variant);
                break;
        }
    }

    applyButtonStyleVariant(variant) {
        const style = document.createElement('style');
        style.id = 'ab-test-button-style';
        
        switch (variant) {
            case 'rounded':
                style.textContent = `
                    .btn-cer-primary {
                        border-radius: 25px !important;
                    }
                    .btn-cer-secondary {
                        border-radius: 25px !important;
                    }
                `;
                break;
            case 'shadow':
                style.textContent = `
                    .btn-cer-primary {
                        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
                    }
                    .btn-cer-secondary {
                        box-shadow: 0 4px 15px rgba(107, 114, 128, 0.3) !important;
                    }
                `;
                break;
        }
        
        if (style.textContent) {
            document.head.appendChild(style);
        }
    }

    applyCardLayoutVariant(variant) {
        const style = document.createElement('style');
        style.id = 'ab-test-card-layout';
        
        switch (variant) {
            case 'compact':
                style.textContent = `
                    .cer-card {
                        padding: 1rem !important;
                        margin-bottom: 1rem !important;
                    }
                    .cer-card-header {
                        margin-bottom: 0.5rem !important;
                    }
                `;
                break;
            case 'expanded':
                style.textContent = `
                    .cer-card {
                        padding: 2rem !important;
                        margin-bottom: 2rem !important;
                    }
                    .cer-card-header {
                        margin-bottom: 1.5rem !important;
                    }
                `;
                break;
        }
        
        if (style.textContent) {
            document.head.appendChild(style);
        }
    }

    applyColorSchemeVariant(variant) {
        const style = document.createElement('style');
        style.id = 'ab-test-color-scheme';
        
        switch (variant) {
            case 'warm':
                style.textContent = `
                    :root {
                        --cer-primary: #f59e0b;
                        --cer-primary-dark: #d97706;
                        --cer-primary-light: #fbbf24;
                    }
                `;
                break;
            case 'cool':
                style.textContent = `
                    :root {
                        --cer-primary: #06b6d4;
                        --cer-primary-dark: #0891b2;
                        --cer-primary-light: #22d3ee;
                    }
                `;
                break;
        }
        
        if (style.textContent) {
            document.head.appendChild(style);
        }
    }

    recordParticipation(experimentId, variant) {
        const participation = {
            experimentId: experimentId,
            variant: variant,
            userId: this.userId,
            timestamp: Date.now(),
            url: window.location.href
        };

        // Salva localmente
        const participations = JSON.parse(localStorage.getItem('ab_testing_participations') || '[]');
        participations.push(participation);
        localStorage.setItem('ab_testing_participations', JSON.stringify(participations));

        // Invia al server
        this.sendParticipationToServer(participation);
    }

    monitorResults() {
        // Monitora click sui bottoni
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-cer-primary') || e.target.classList.contains('btn-cer-secondary')) {
                this.recordEvent('button_click', {
                    buttonClass: e.target.className,
                    buttonText: e.target.textContent,
                    timestamp: Date.now()
                });
            }
        });

        // Monitora tempo su pagina
        let pageTime = 0;
        setInterval(() => {
            pageTime += 1000;
            this.recordEvent('page_time', {
                time: pageTime,
                timestamp: Date.now()
            });
        }, 10000); // Ogni 10 secondi

        // Monitora scroll depth
        let maxScrollDepth = 0;
        window.addEventListener('scroll', () => {
            const scrollDepth = (window.scrollY + window.innerHeight) / document.body.scrollHeight;
            if (scrollDepth > maxScrollDepth) {
                maxScrollDepth = scrollDepth;
                this.recordEvent('scroll_depth', {
                    depth: maxScrollDepth,
                    timestamp: Date.now()
                });
            }
        });

        // Monitora bounce rate
        let hasInteracted = false;
        document.addEventListener('click', () => { hasInteracted = true; });
        document.addEventListener('scroll', () => { hasInteracted = true; });
        
        window.addEventListener('beforeunload', () => {
            if (!hasInteracted) {
                this.recordEvent('bounce', {
                    timestamp: Date.now()
                });
            }
        });
    }

    recordEvent(eventType, eventData) {
        const event = {
            eventType: eventType,
            eventData: eventData,
            userId: this.userId,
            timestamp: Date.now(),
            url: window.location.href,
            experiments: this.getActiveExperiments()
        };

        // Salva localmente
        const events = JSON.parse(localStorage.getItem('ab_testing_events') || '[]');
        events.push(event);
        localStorage.setItem('ab_testing_events', JSON.stringify(events));

        // Invia al server
        this.sendEventToServer(event);
    }

    getActiveExperiments() {
        const activeExperiments = {};
        Object.keys(this.experiments).forEach(experimentId => {
            const experiment = this.experiments[experimentId];
            if (this.isUserInExperiment(experimentId, experiment)) {
                const variant = this.getUserVariant(experimentId, experiment);
                activeExperiments[experimentId] = variant;
            }
        });
        return activeExperiments;
    }

    sendParticipationToServer(participation) {
        fetch('/api/ab-testing/participation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(participation)
        }).catch(error => {
            console.log('Error sending participation:', error);
        });
    }

    sendEventToServer(event) {
        fetch('/api/ab-testing/event/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(event)
        }).catch(error => {
            console.log('Error sending event:', error);
        });
    }

    // Ottieni risultati esperimenti
    getExperimentResults() {
        const participations = JSON.parse(localStorage.getItem('ab_testing_participations') || '[]');
        const events = JSON.parse(localStorage.getItem('ab_testing_events') || '[]');
        
        return {
            participations: participations,
            events: events,
            activeExperiments: this.getActiveExperiments()
        };
    }

    // Debug: mostra esperimenti attivi
    showActiveExperiments() {
        console.log('=== A/B TESTING EXPERIMENTS ===');
        const activeExperiments = this.getActiveExperiments();
        Object.keys(activeExperiments).forEach(experimentId => {
            console.log(`${experimentId}: ${activeExperiments[experimentId]}`);
        });
        console.log('===============================');
    }
}

// Inizializza A/B testing system
document.addEventListener('DOMContentLoaded', function() {
    const abTestingSystem = new ABTestingSystem();
    
    // Esponi globalmente per debug
    window.abTestingSystem = abTestingSystem;
    
    // Mostra esperimenti attivi in console
    setTimeout(() => {
        abTestingSystem.showActiveExperiments();
    }, 1000);
});
