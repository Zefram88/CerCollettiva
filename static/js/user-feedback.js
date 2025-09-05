/**
 * User Feedback System - CerCollettiva
 * Sistema per raccogliere feedback utenti e migliorare UX
 */

class UserFeedbackSystem {
    constructor() {
        this.feedbackData = {
            sessionId: this.generateSessionId(),
            startTime: Date.now(),
            interactions: [],
            ratings: {},
            comments: [],
            issues: [],
            suggestions: []
        };
        this.init();
    }

    init() {
        // Raccogli feedback automatico
        this.collectAutomaticFeedback();
        
        // Inizializza feedback widget
        this.createFeedbackWidget();
        
        // Monitora interazioni utente
        this.monitorUserInteractions();
        
        // Raccogli feedback al termine sessione
        this.collectSessionFeedback();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    collectAutomaticFeedback() {
        // Monitora tempo di caricamento
        window.addEventListener('load', () => {
            const loadTime = Date.now() - this.feedbackData.startTime;
            this.feedbackData.loadTime = loadTime;
            
            // Valuta performance
            if (loadTime < 2000) {
                this.feedbackData.performanceRating = 'excellent';
            } else if (loadTime < 4000) {
                this.feedbackData.performanceRating = 'good';
            } else if (loadTime < 6000) {
                this.feedbackData.performanceRating = 'fair';
            } else {
                this.feedbackData.performanceRating = 'poor';
            }
        });

        // Monitora errori
        window.addEventListener('error', (e) => {
            this.feedbackData.issues.push({
                type: 'javascript_error',
                message: e.message,
                filename: e.filename,
                line: e.lineno,
                timestamp: Date.now()
            });
        });

        // Monitora errori di rete
        window.addEventListener('unhandledrejection', (e) => {
            this.feedbackData.issues.push({
                type: 'promise_rejection',
                message: e.reason,
                timestamp: Date.now()
            });
        });
    }

    createFeedbackWidget() {
        // Crea widget feedback
        const widget = document.createElement('div');
        widget.id = 'feedback-widget';
        widget.innerHTML = `
            <div class="feedback-widget">
                <button id="feedback-trigger" class="feedback-trigger" title="Invia feedback">
                    <i class="fas fa-comment-dots"></i>
                </button>
                <div id="feedback-modal" class="feedback-modal" style="display: none;">
                    <div class="feedback-modal-content">
                        <div class="feedback-header">
                            <h3>Feedback</h3>
                            <button id="feedback-close" class="feedback-close">&times;</button>
                        </div>
                        <div class="feedback-body">
                            <div class="feedback-section">
                                <h4>Come valuti la tua esperienza?</h4>
                                <div class="rating-buttons">
                                    <button class="rating-btn" data-rating="1" title="Molto insoddisfatto">
                                        <i class="fas fa-frown"></i>
                                    </button>
                                    <button class="rating-btn" data-rating="2" title="Insoddisfatto">
                                        <i class="fas fa-meh"></i>
                                    </button>
                                    <button class="rating-btn" data-rating="3" title="Neutro">
                                        <i class="fas fa-smile"></i>
                                    </button>
                                    <button class="rating-btn" data-rating="4" title="Soddisfatto">
                                        <i class="fas fa-laugh"></i>
                                    </button>
                                    <button class="rating-btn" data-rating="5" title="Molto soddisfatto">
                                        <i class="fas fa-heart"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="feedback-section">
                                <h4>Hai riscontrato problemi?</h4>
                                <textarea id="feedback-issues" placeholder="Descrivi eventuali problemi riscontrati..."></textarea>
                            </div>
                            <div class="feedback-section">
                                <h4>Suggerimenti per migliorare</h4>
                                <textarea id="feedback-suggestions" placeholder="Hai suggerimenti per migliorare l'applicazione?"></textarea>
                            </div>
                            <div class="feedback-section">
                                <h4>Commenti aggiuntivi</h4>
                                <textarea id="feedback-comments" placeholder="Altri commenti..."></textarea>
                            </div>
                        </div>
                        <div class="feedback-footer">
                            <button id="feedback-submit" class="btn btn-primary">Invia Feedback</button>
                            <button id="feedback-cancel" class="btn btn-secondary">Annulla</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Aggiungi CSS
        const style = document.createElement('style');
        style.textContent = `
            .feedback-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }

            .feedback-trigger {
                background: var(--cer-primary);
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                transition: all 0.3s ease;
            }

            .feedback-trigger:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
            }

            .feedback-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1001;
            }

            .feedback-modal-content {
                background: white;
                border-radius: 12px;
                width: 90%;
                max-width: 500px;
                max-height: 80vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            }

            .feedback-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                border-bottom: 1px solid #eee;
            }

            .feedback-header h3 {
                margin: 0;
                color: var(--cer-primary);
            }

            .feedback-close {
                background: none;
                border: none;
                font-size: 24px;
                cursor: pointer;
                color: #666;
            }

            .feedback-body {
                padding: 20px;
            }

            .feedback-section {
                margin-bottom: 20px;
            }

            .feedback-section h4 {
                margin-bottom: 10px;
                color: var(--cer-gray-700);
            }

            .rating-buttons {
                display: flex;
                gap: 10px;
                justify-content: center;
            }

            .rating-btn {
                background: none;
                border: 2px solid #ddd;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                font-size: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .rating-btn:hover {
                border-color: var(--cer-primary);
                transform: scale(1.1);
            }

            .rating-btn.selected {
                border-color: var(--cer-primary);
                background: var(--cer-primary);
                color: white;
            }

            .feedback-section textarea {
                width: 100%;
                min-height: 80px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 6px;
                resize: vertical;
                font-family: inherit;
            }

            .feedback-footer {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                padding: 20px;
                border-top: 1px solid #eee;
            }

            @media (max-width: 768px) {
                .feedback-modal-content {
                    width: 95%;
                    margin: 20px;
                }
                
                .rating-buttons {
                    flex-wrap: wrap;
                }
                
                .rating-btn {
                    width: 40px;
                    height: 40px;
                    font-size: 16px;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(widget);

        // Aggiungi event listeners
        this.addFeedbackEventListeners();
    }

    addFeedbackEventListeners() {
        const trigger = document.getElementById('feedback-trigger');
        const modal = document.getElementById('feedback-modal');
        const close = document.getElementById('feedback-close');
        const cancel = document.getElementById('feedback-cancel');
        const submit = document.getElementById('feedback-submit');
        const ratingButtons = document.querySelectorAll('.rating-btn');

        // Apri modal
        trigger.addEventListener('click', () => {
            modal.style.display = 'flex';
        });

        // Chiudi modal
        close.addEventListener('click', () => this.closeFeedbackModal());
        cancel.addEventListener('click', () => this.closeFeedbackModal());

        // Click fuori modal
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeFeedbackModal();
            }
        });

        // Rating buttons
        ratingButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                ratingButtons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                this.feedbackData.overallRating = parseInt(btn.dataset.rating);
            });
        });

        // Submit feedback
        submit.addEventListener('click', () => {
            this.submitFeedback();
        });
    }

    closeFeedbackModal() {
        const modal = document.getElementById('feedback-modal');
        modal.style.display = 'none';
    }

    submitFeedback() {
        // Raccogli dati feedback
        const issues = document.getElementById('feedback-issues').value;
        const suggestions = document.getElementById('feedback-suggestions').value;
        const comments = document.getElementById('feedback-comments').value;

        if (issues) {
            this.feedbackData.issues.push({
                type: 'user_reported',
                message: issues,
                timestamp: Date.now()
            });
        }

        if (suggestions) {
            this.feedbackData.suggestions.push({
                message: suggestions,
                timestamp: Date.now()
            });
        }

        if (comments) {
            this.feedbackData.comments.push({
                message: comments,
                timestamp: Date.now()
            });
        }

        // Invia feedback
        this.sendFeedbackToServer();

        // Chiudi modal
        this.closeFeedbackModal();

        // Mostra conferma
        this.showFeedbackConfirmation();
    }

    showFeedbackConfirmation() {
        const notification = document.createElement('div');
        notification.className = 'feedback-notification';
        notification.innerHTML = `
            <div class="feedback-notification-content">
                <i class="fas fa-check-circle"></i>
                <span>Grazie per il tuo feedback!</span>
            </div>
        `;

        // Aggiungi CSS per notifica
        const style = document.createElement('style');
        style.textContent = `
            .feedback-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1002;
                animation: slideIn 0.3s ease;
            }

            .feedback-notification-content {
                background: var(--cer-success);
                color: white;
                padding: 15px 20px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            }

            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(notification);

        // Rimuovi notifica dopo 3 secondi
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    monitorUserInteractions() {
        // Monitora click
        document.addEventListener('click', (e) => {
            this.feedbackData.interactions.push({
                type: 'click',
                target: e.target.tagName,
                className: e.target.className,
                id: e.target.id,
                timestamp: Date.now()
            });
        });

        // Monitora scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.feedbackData.interactions.push({
                    type: 'scroll',
                    scrollY: window.scrollY,
                    timestamp: Date.now()
                });
            }, 100);
        });

        // Monitora tempo su pagina
        let pageTime = 0;
        setInterval(() => {
            pageTime += 1000;
            this.feedbackData.pageTime = pageTime;
        }, 1000);
    }

    collectSessionFeedback() {
        // Raccogli feedback al termine sessione
        window.addEventListener('beforeunload', () => {
            this.feedbackData.endTime = Date.now();
            this.feedbackData.sessionDuration = this.feedbackData.endTime - this.feedbackData.startTime;
            
            // Invia dati sessione
            this.sendSessionDataToServer();
        });

        // Raccogli feedback ogni 5 minuti
        setInterval(() => {
            this.sendSessionDataToServer();
        }, 300000); // 5 minuti
    }

    sendFeedbackToServer() {
        const feedbackData = {
            ...this.feedbackData,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`
        };

        fetch('/api/user-feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(feedbackData)
        }).catch(error => {
            console.log('Error sending feedback:', error);
        });
    }

    sendSessionDataToServer() {
        const sessionData = {
            sessionId: this.feedbackData.sessionId,
            startTime: this.feedbackData.startTime,
            endTime: this.feedbackData.endTime || Date.now(),
            sessionDuration: this.feedbackData.sessionDuration || (Date.now() - this.feedbackData.startTime),
            pageTime: this.feedbackData.pageTime || 0,
            interactions: this.feedbackData.interactions.length,
            issues: this.feedbackData.issues.length,
            performanceRating: this.feedbackData.performanceRating,
            overallRating: this.feedbackData.overallRating,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        fetch('/api/session-data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(sessionData)
        }).catch(error => {
            console.log('Error sending session data:', error);
        });
    }

    // Ottieni dati feedback
    getFeedbackData() {
        return this.feedbackData;
    }
}

// Inizializza user feedback system
document.addEventListener('DOMContentLoaded', function() {
    const userFeedbackSystem = new UserFeedbackSystem();
    
    // Esponi globalmente per debug
    window.userFeedbackSystem = userFeedbackSystem;
});
