/**
 * Accessibility Audit - CerCollettiva
 * Verifica e migliora l'accessibilità dell'applicazione
 */

class AccessibilityAudit {
    constructor() {
        this.issues = [];
        this.init();
    }

    init() {
        // Esegui audit dopo il caricamento completo
        setTimeout(() => {
            this.runAudit();
            this.logResults();
        }, 2000);
    }

    runAudit() {
        // Verifica elementi con focus
        this.checkFocusElements();
        
        // Verifica contrasti colori
        this.checkColorContrast();
        
        // Verifica alt text per immagini
        this.checkImageAltText();
        
        // Verifica heading structure
        this.checkHeadingStructure();
        
        // Verifica form labels
        this.checkFormLabels();
        
        // Verifica ARIA attributes
        this.checkAriaAttributes();
        
        // Verifica keyboard navigation
        this.checkKeyboardNavigation();
        
        // Verifica screen reader support
        this.checkScreenReaderSupport();
    }

    checkFocusElements() {
        const focusableElements = document.querySelectorAll(
            'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        focusableElements.forEach(element => {
            // Verifica se l'elemento è visibile
            if (!this.isElementVisible(element)) {
                this.issues.push({
                    type: 'focus',
                    severity: 'warning',
                    message: 'Elemento focusabile non visibile',
                    element: element
                });
            }
            
            // Verifica se l'elemento ha indicatore di focus
            if (!this.hasFocusIndicator(element)) {
                this.issues.push({
                    type: 'focus',
                    severity: 'error',
                    message: 'Elemento senza indicatore di focus visibile',
                    element: element
                });
            }
        });
    }

    checkColorContrast() {
        const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, button');
        
        textElements.forEach(element => {
            const styles = window.getComputedStyle(element);
            const color = styles.color;
            const backgroundColor = styles.backgroundColor;
            
            if (color && backgroundColor && color !== 'rgba(0, 0, 0, 0)' && backgroundColor !== 'rgba(0, 0, 0, 0)') {
                const contrast = this.calculateContrast(color, backgroundColor);
                
                if (contrast < 4.5) {
                    this.issues.push({
                        type: 'contrast',
                        severity: 'error',
                        message: `Contrasto insufficiente: ${contrast.toFixed(2)}:1`,
                        element: element
                    });
                } else if (contrast < 7) {
                    this.issues.push({
                        type: 'contrast',
                        severity: 'warning',
                        message: `Contrasto migliorabile: ${contrast.toFixed(2)}:1`,
                        element: element
                    });
                }
            }
        });
    }

    checkImageAltText() {
        const images = document.querySelectorAll('img');
        
        images.forEach(img => {
            if (!img.alt || img.alt.trim() === '') {
                this.issues.push({
                    type: 'image',
                    severity: 'error',
                    message: 'Immagine senza alt text',
                    element: img
                });
            }
        });
    }

    checkHeadingStructure() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        let previousLevel = 0;
        
        headings.forEach(heading => {
            const currentLevel = parseInt(heading.tagName.charAt(1));
            
            if (currentLevel > previousLevel + 1) {
                this.issues.push({
                    type: 'heading',
                    severity: 'warning',
                    message: `Salto di livello heading: da H${previousLevel} a H${currentLevel}`,
                    element: heading
                });
            }
            
            previousLevel = currentLevel;
        });
    }

    checkFormLabels() {
        const inputs = document.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            const id = input.id;
            const label = document.querySelector(`label[for="${id}"]`);
            const ariaLabel = input.getAttribute('aria-label');
            const ariaLabelledBy = input.getAttribute('aria-labelledby');
            
            if (!label && !ariaLabel && !ariaLabelledBy) {
                this.issues.push({
                    type: 'form',
                    severity: 'error',
                    message: 'Input senza label associato',
                    element: input
                });
            }
        });
    }

    checkAriaAttributes() {
        const elementsWithAria = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby]');
        
        elementsWithAria.forEach(element => {
            const ariaLabel = element.getAttribute('aria-label');
            const ariaLabelledBy = element.getAttribute('aria-labelledby');
            const ariaDescribedBy = element.getAttribute('aria-describedby');
            
            // Verifica se aria-labelledby punta a elementi esistenti
            if (ariaLabelledBy) {
                const labelledByElement = document.getElementById(ariaLabelledBy);
                if (!labelledByElement) {
                    this.issues.push({
                        type: 'aria',
                        severity: 'error',
                        message: 'aria-labelledby punta a elemento inesistente',
                        element: element
                    });
                }
            }
            
            // Verifica se aria-describedby punta a elementi esistenti
            if (ariaDescribedBy) {
                const describedByElement = document.getElementById(ariaDescribedBy);
                if (!describedByElement) {
                    this.issues.push({
                        type: 'aria',
                        severity: 'error',
                        message: 'aria-describedby punta a elemento inesistente',
                        element: element
                    });
                }
            }
        });
    }

    checkKeyboardNavigation() {
        // Verifica se tutti gli elementi interattivi sono raggiungibili con Tab
        const focusableElements = document.querySelectorAll(
            'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        let tabOrder = [];
        focusableElements.forEach(element => {
            const tabIndex = element.tabIndex;
            tabOrder.push({ element, tabIndex });
        });
        
        // Verifica ordine tab
        tabOrder.sort((a, b) => a.tabIndex - b.tabIndex);
        
        for (let i = 0; i < tabOrder.length - 1; i++) {
            if (tabOrder[i].tabIndex > 0 && tabOrder[i + 1].tabIndex > 0) {
                if (tabOrder[i].tabIndex > tabOrder[i + 1].tabIndex) {
                    this.issues.push({
                        type: 'keyboard',
                        severity: 'warning',
                        message: 'Ordine tab non logico',
                        element: tabOrder[i].element
                    });
                }
            }
        }
    }

    checkScreenReaderSupport() {
        // Verifica se ci sono elementi che potrebbero essere problematici per screen reader
        const elementsWithRole = document.querySelectorAll('[role]');
        
        elementsWithRole.forEach(element => {
            const role = element.getAttribute('role');
            
            // Verifica se il ruolo è appropriato
            if (role === 'button' && element.tagName !== 'BUTTON') {
                if (!element.getAttribute('tabindex')) {
                    this.issues.push({
                        type: 'screen-reader',
                        severity: 'warning',
                        message: 'Elemento con role="button" senza tabindex',
                        element: element
                    });
                }
            }
        });
    }

    isElementVisible(element) {
        const styles = window.getComputedStyle(element);
        return styles.display !== 'none' && 
               styles.visibility !== 'hidden' && 
               styles.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }

    hasFocusIndicator(element) {
        const styles = window.getComputedStyle(element);
        return styles.outline !== 'none' || 
               styles.boxShadow !== 'none' ||
               element.classList.contains('focus-visible');
    }

    calculateContrast(color1, color2) {
        // Conversione semplificata per calcolo contrasto
        const rgb1 = this.hexToRgb(color1);
        const rgb2 = this.hexToRgb(color2);
        
        if (!rgb1 || !rgb2) return 0;
        
        const luminance1 = this.getLuminance(rgb1);
        const luminance2 = this.getLuminance(rgb2);
        
        const lighter = Math.max(luminance1, luminance2);
        const darker = Math.min(luminance1, luminance2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    hexToRgb(hex) {
        // Conversione semplificata per colori CSS
        if (hex.startsWith('rgb')) {
            const matches = hex.match(/\d+/g);
            if (matches && matches.length >= 3) {
                return {
                    r: parseInt(matches[0]),
                    g: parseInt(matches[1]),
                    b: parseInt(matches[2])
                };
            }
        }
        return null;
    }

    getLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }

    logResults() {
        console.log('=== ACCESSIBILITY AUDIT ===');
        console.log(`Totale problemi trovati: ${this.issues.length}`);
        
        const errors = this.issues.filter(issue => issue.severity === 'error');
        const warnings = this.issues.filter(issue => issue.severity === 'warning');
        
        console.log(`Errori: ${errors.length}`);
        console.log(`Warning: ${warnings.length}`);
        
        if (errors.length > 0) {
            console.log('\n--- ERRORI ---');
            errors.forEach(issue => {
                console.error(`${issue.type.toUpperCase()}: ${issue.message}`, issue.element);
            });
        }
        
        if (warnings.length > 0) {
            console.log('\n--- WARNING ---');
            warnings.forEach(issue => {
                console.warn(`${issue.type.toUpperCase()}: ${issue.message}`, issue.element);
            });
        }
        
        console.log('==========================');
        
        // Invia risultati al server (opzionale)
        this.sendResultsToServer();
    }

    sendResultsToServer() {
        if (this.issues.length > 0) {
            const results = {
                timestamp: new Date().toISOString(),
                totalIssues: this.issues.length,
                errors: this.issues.filter(issue => issue.severity === 'error').length,
                warnings: this.issues.filter(issue => issue.severity === 'warning').length,
                issues: this.issues.map(issue => ({
                    type: issue.type,
                    severity: issue.severity,
                    message: issue.message,
                    element: issue.element.tagName + (issue.element.id ? '#' + issue.element.id : '')
                }))
            };
            
            fetch('/api/accessibility-audit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(results)
            }).catch(error => {
                console.log('Error sending accessibility audit results:', error);
            });
        }
    }

    // Ottieni risultati audit
    getResults() {
        return {
            totalIssues: this.issues.length,
            errors: this.issues.filter(issue => issue.severity === 'error'),
            warnings: this.issues.filter(issue => issue.severity === 'warning'),
            allIssues: this.issues
        };
    }
}

// Inizializza accessibility audit
document.addEventListener('DOMContentLoaded', function() {
    const accessibilityAudit = new AccessibilityAudit();
    
    // Esponi globalmente per debug
    window.accessibilityAudit = accessibilityAudit;
});
