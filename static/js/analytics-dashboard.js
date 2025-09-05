/**
 * Analytics Dashboard - CerCollettiva
 * Dashboard per visualizzare metriche e analytics in tempo reale
 */

class AnalyticsDashboard {
    constructor() {
        this.metrics = {
            performance: {},
            user: {},
            device: {},
            accessibility: {},
            feedback: {},
            abTesting: {}
        };
        this.init();
    }

    init() {
        console.log('Analytics Dashboard: Initializing (dashboard will NOT be created automatically)');
        
        // Raccogli metriche da tutti i sistemi
        this.collectMetrics();
        
        // NON creare dashboard automaticamente
        // this.createDashboard();
        
        // Aggiorna metriche ogni 30 secondi solo se dashboard è visibile
        setInterval(() => {
            this.collectMetrics();
            if (document.getElementById('analytics-dashboard')) {
                this.updateDashboard();
            }
        }, 30000);
        
        console.log('Analytics Dashboard: Initialization complete. Use Ctrl+Shift+A to open dashboard.');
    }

    collectMetrics() {
        // Raccogli metriche performance
        if (window.performanceMonitor) {
            this.metrics.performance = window.performanceMonitor.getMetrics();
        }

        // Raccogli metriche device
        if (window.deviceDetector) {
            this.metrics.device = window.deviceDetector.getDeviceInfo();
        }

        // Raccogli metriche accessibilità
        if (window.accessibilityAudit) {
            this.metrics.accessibility = window.accessibilityAudit.getResults();
        }

        // Raccogli metriche feedback
        if (window.userFeedbackSystem) {
            this.metrics.feedback = window.userFeedbackSystem.getFeedbackData();
        }

        // Raccogli metriche A/B testing
        if (window.abTestingSystem) {
            this.metrics.abTesting = window.abTestingSystem.getExperimentResults();
        }

        // Raccogli metriche utente
        this.metrics.user = {
            sessionId: this.metrics.feedback.sessionId || 'unknown',
            startTime: this.metrics.feedback.startTime || Date.now(),
            pageTime: this.metrics.feedback.pageTime || 0,
            interactions: this.metrics.feedback.interactions?.length || 0,
            url: window.location.href,
            referrer: document.referrer,
            timestamp: Date.now()
        };
    }

    createDashboard() {
        // Crea dashboard solo se non esiste
        if (document.getElementById('analytics-dashboard')) {
            return;
        }
        
        // Verifica che non ci siano altri dashboard
        const existingDashboards = document.querySelectorAll('.analytics-dashboard');
        if (existingDashboards.length > 0) {
            existingDashboards.forEach(dashboard => dashboard.remove());
        }

        const dashboard = document.createElement('div');
        dashboard.id = 'analytics-dashboard';
        dashboard.innerHTML = `
            <div class="analytics-dashboard">
                <div class="analytics-header">
                    <h3>Analytics Dashboard</h3>
                    <button id="analytics-close" class="analytics-close">&times;</button>
                </div>
                <div class="analytics-content">
                    <div class="analytics-tabs">
                        <button class="analytics-tab active" data-tab="performance">Performance</button>
                        <button class="analytics-tab" data-tab="user">User</button>
                        <button class="analytics-tab" data-tab="device">Device</button>
                        <button class="analytics-tab" data-tab="accessibility">Accessibility</button>
                        <button class="analytics-tab" data-tab="feedback">Feedback</button>
                        <button class="analytics-tab" data-tab="ab-testing">A/B Testing</button>
                    </div>
                    <div class="analytics-tab-content">
                        <div id="tab-performance" class="analytics-tab-panel active">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>LCP</h4>
                                    <div class="metric-value" id="lcp-value">-</div>
                                    <div class="metric-label">Largest Contentful Paint</div>
                                </div>
                                <div class="metric-card">
                                    <h4>FID</h4>
                                    <div class="metric-value" id="fid-value">-</div>
                                    <div class="metric-label">First Input Delay</div>
                                </div>
                                <div class="metric-card">
                                    <h4>CLS</h4>
                                    <div class="metric-value" id="cls-value">-</div>
                                    <div class="metric-label">Cumulative Layout Shift</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Memory</h4>
                                    <div class="metric-value" id="memory-value">-</div>
                                    <div class="metric-label">Memory Usage</div>
                                </div>
                            </div>
                        </div>
                        <div id="tab-user" class="analytics-tab-panel">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>Session Time</h4>
                                    <div class="metric-value" id="session-time-value">-</div>
                                    <div class="metric-label">Time on Page</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Interactions</h4>
                                    <div class="metric-value" id="interactions-value">-</div>
                                    <div class="metric-label">User Interactions</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Page URL</h4>
                                    <div class="metric-value" id="page-url-value">-</div>
                                    <div class="metric-label">Current Page</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Referrer</h4>
                                    <div class="metric-value" id="referrer-value">-</div>
                                    <div class="metric-label">Traffic Source</div>
                                </div>
                            </div>
                        </div>
                        <div id="tab-device" class="analytics-tab-panel">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>Device Type</h4>
                                    <div class="metric-value" id="device-type-value">-</div>
                                    <div class="metric-label">Device Category</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Operating System</h4>
                                    <div class="metric-value" id="os-value">-</div>
                                    <div class="metric-label">OS</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Browser</h4>
                                    <div class="metric-value" id="browser-value">-</div>
                                    <div class="metric-label">Browser</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Screen Size</h4>
                                    <div class="metric-value" id="screen-size-value">-</div>
                                    <div class="metric-label">Resolution</div>
                                </div>
                            </div>
                        </div>
                        <div id="tab-accessibility" class="analytics-tab-panel">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>Total Issues</h4>
                                    <div class="metric-value" id="accessibility-issues-value">-</div>
                                    <div class="metric-label">Accessibility Issues</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Errors</h4>
                                    <div class="metric-value" id="accessibility-errors-value">-</div>
                                    <div class="metric-label">Critical Issues</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Warnings</h4>
                                    <div class="metric-value" id="accessibility-warnings-value">-</div>
                                    <div class="metric-label">Warning Issues</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Score</h4>
                                    <div class="metric-value" id="accessibility-score-value">-</div>
                                    <div class="metric-label">Accessibility Score</div>
                                </div>
                            </div>
                        </div>
                        <div id="tab-feedback" class="analytics-tab-panel">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>Overall Rating</h4>
                                    <div class="metric-value" id="overall-rating-value">-</div>
                                    <div class="metric-label">User Satisfaction</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Performance Rating</h4>
                                    <div class="metric-value" id="performance-rating-value">-</div>
                                    <div class="metric-label">Performance Score</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Issues Reported</h4>
                                    <div class="metric-value" id="issues-reported-value">-</div>
                                    <div class="metric-label">User Issues</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Suggestions</h4>
                                    <div class="metric-value" id="suggestions-value">-</div>
                                    <div class="metric-label">User Suggestions</div>
                                </div>
                            </div>
                        </div>
                        <div id="tab-ab-testing" class="analytics-tab-panel">
                            <div class="metrics-grid">
                                <div class="metric-card">
                                    <h4>Active Experiments</h4>
                                    <div class="metric-value" id="active-experiments-value">-</div>
                                    <div class="metric-label">Running Tests</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Participations</h4>
                                    <div class="metric-value" id="participations-value">-</div>
                                    <div class="metric-label">Test Participations</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Events</h4>
                                    <div class="metric-value" id="events-value">-</div>
                                    <div class="metric-label">Tracked Events</div>
                                </div>
                                <div class="metric-card">
                                    <h4>Variants</h4>
                                    <div class="metric-value" id="variants-value">-</div>
                                    <div class="metric-label">Active Variants</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Aggiungi CSS
        const style = document.createElement('style');
        style.textContent = `
            .analytics-dashboard {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 90%;
                max-width: 800px;
                max-height: 80vh;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                z-index: 1003;
                overflow: hidden;
                display: none; /* Nascosto di default */
                pointer-events: auto; /* Assicura che gli eventi funzionino */
            }

            .analytics-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                background: var(--cer-primary);
                color: white;
            }

            .analytics-header h3 {
                margin: 0;
            }

            .analytics-close {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
            }

            .analytics-content {
                padding: 20px;
            }

            .analytics-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #eee;
            }

            .analytics-tab {
                background: none;
                border: none;
                padding: 10px 20px;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                transition: all 0.3s ease;
            }

            .analytics-tab.active {
                border-bottom-color: var(--cer-primary);
                color: var(--cer-primary);
            }

            .analytics-tab-panel {
                display: none;
            }

            .analytics-tab-panel.active {
                display: block;
            }

            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }

            .metric-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }

            .metric-card h4 {
                margin: 0 0 10px 0;
                color: var(--cer-gray-700);
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: var(--cer-primary);
                margin-bottom: 5px;
            }

            .metric-label {
                font-size: 12px;
                color: var(--cer-gray-500);
            }

            @media (max-width: 768px) {
                .analytics-dashboard {
                    width: 95%;
                    max-height: 90vh;
                }
                
                .metrics-grid {
                    grid-template-columns: 1fr;
                }
                
                .analytics-tabs {
                    flex-wrap: wrap;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(dashboard);

        // Aggiungi event listeners
        this.addDashboardEventListeners();
    }

    addDashboardEventListeners() {
        const close = document.getElementById('analytics-close');
        const tabs = document.querySelectorAll('.analytics-tab');
        const panels = document.querySelectorAll('.analytics-tab-panel');

        // Chiudi dashboard
        close.addEventListener('click', () => {
            document.getElementById('analytics-dashboard').remove();
        });

        // Cambia tab
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabId = tab.dataset.tab;
                
                // Rimuovi active da tutti i tab
                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                
                // Aggiungi active al tab selezionato
                tab.classList.add('active');
                document.getElementById(`tab-${tabId}`).classList.add('active');
            });
        });
    }

    updateDashboard() {
        // Aggiorna metriche performance
        this.updatePerformanceMetrics();
        
        // Aggiorna metriche utente
        this.updateUserMetrics();
        
        // Aggiorna metriche device
        this.updateDeviceMetrics();
        
        // Aggiorna metriche accessibilità
        this.updateAccessibilityMetrics();
        
        // Aggiorna metriche feedback
        this.updateFeedbackMetrics();
        
        // Aggiorna metriche A/B testing
        this.updateABTestingMetrics();
    }

    updatePerformanceMetrics() {
        const lcp = this.metrics.performance.lcp;
        const fid = this.metrics.performance.fid;
        const cls = this.metrics.performance.cls;
        const memory = this.metrics.performance.memory;

        document.getElementById('lcp-value').textContent = lcp ? `${lcp.toFixed(0)}ms` : '-';
        document.getElementById('fid-value').textContent = fid ? `${fid.toFixed(0)}ms` : '-';
        document.getElementById('cls-value').textContent = cls ? cls.toFixed(3) : '-';
        document.getElementById('memory-value').textContent = memory ? `${Math.round(memory.used / 1024 / 1024)}MB` : '-';
    }

    updateUserMetrics() {
        const sessionTime = this.metrics.user.pageTime;
        const interactions = this.metrics.user.interactions;
        const url = this.metrics.user.url;
        const referrer = this.metrics.user.referrer;

        document.getElementById('session-time-value').textContent = sessionTime ? `${Math.round(sessionTime / 1000)}s` : '-';
        document.getElementById('interactions-value').textContent = interactions || '0';
        document.getElementById('page-url-value').textContent = url ? url.split('/').pop() : '-';
        document.getElementById('referrer-value').textContent = referrer ? referrer.split('/')[2] : 'Direct';
    }

    updateDeviceMetrics() {
        const device = this.metrics.device.device;
        const browser = this.metrics.device.browser;
        const capabilities = this.metrics.device.capabilities;

        document.getElementById('device-type-value').textContent = device ? device.type : '-';
        document.getElementById('os-value').textContent = device ? device.os : '-';
        document.getElementById('browser-value').textContent = browser ? browser.name : '-';
        document.getElementById('screen-size-value').textContent = capabilities ? `${capabilities.screen.width}x${capabilities.screen.height}` : '-';
    }

    updateAccessibilityMetrics() {
        const totalIssues = this.metrics.accessibility.totalIssues || 0;
        const errors = this.metrics.accessibility.errors?.length || 0;
        const warnings = this.metrics.accessibility.warnings?.length || 0;
        const score = totalIssues > 0 ? Math.max(0, 100 - (errors * 10) - (warnings * 5)) : 100;

        document.getElementById('accessibility-issues-value').textContent = totalIssues;
        document.getElementById('accessibility-errors-value').textContent = errors;
        document.getElementById('accessibility-warnings-value').textContent = warnings;
        document.getElementById('accessibility-score-value').textContent = `${score}/100`;
    }

    updateFeedbackMetrics() {
        const overallRating = this.metrics.feedback.overallRating;
        const performanceRating = this.metrics.feedback.performanceRating;
        const issues = this.metrics.feedback.issues?.length || 0;
        const suggestions = this.metrics.feedback.suggestions?.length || 0;

        document.getElementById('overall-rating-value').textContent = overallRating ? `${overallRating}/5` : '-';
        document.getElementById('performance-rating-value').textContent = performanceRating || '-';
        document.getElementById('issues-reported-value').textContent = issues;
        document.getElementById('suggestions-value').textContent = suggestions;
    }

    updateABTestingMetrics() {
        const activeExperiments = Object.keys(this.metrics.abTesting.activeExperiments || {}).length;
        const participations = this.metrics.abTesting.participations?.length || 0;
        const events = this.metrics.abTesting.events?.length || 0;
        const variants = Object.values(this.metrics.abTesting.activeExperiments || {}).length;

        document.getElementById('active-experiments-value').textContent = activeExperiments;
        document.getElementById('participations-value').textContent = participations;
        document.getElementById('events-value').textContent = events;
        document.getElementById('variants-value').textContent = variants;
    }

    // Mostra dashboard
    show() {
        console.log('Analytics Dashboard: show() called');
        if (!document.getElementById('analytics-dashboard')) {
            console.log('Analytics Dashboard: Creating new dashboard');
            this.createDashboard();
        }
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            console.log('Analytics Dashboard: Showing dashboard');
            dashboard.style.display = 'flex';
            // Aggiorna metriche quando si apre
            this.updateDashboard();
        }
    }

    // Nascondi dashboard
    hide() {
        const dashboard = document.getElementById('analytics-dashboard');
        if (dashboard) {
            dashboard.remove();
        }
    }
}

// Inizializza analytics dashboard
document.addEventListener('DOMContentLoaded', function() {
    const analyticsDashboard = new AnalyticsDashboard();
    
    // Esponi globalmente per debug
    window.analyticsDashboard = analyticsDashboard;
    
    // Aggiungi shortcut da tastiera per aprire dashboard
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            analyticsDashboard.show();
        }
    });
});
