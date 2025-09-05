/**
 * Performance Monitor - CerCollettiva
 * Monitora Core Web Vitals e performance dell'applicazione
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        // Monitora Core Web Vitals
        this.monitorLCP();
        this.monitorFID();
        this.monitorCLS();
        this.monitorFCP();
        this.monitorTTFB();
        
        // Monitora performance custom
        this.monitorCustomMetrics();
        
        // Log performance data
        this.logPerformanceData();
    }

    // Largest Contentful Paint
    monitorLCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.lcp = lastEntry.startTime;
                console.log('LCP:', lastEntry.startTime + 'ms');
            });
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        }
    }

    // First Input Delay
    monitorFID() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    this.metrics.fid = entry.processingStart - entry.startTime;
                    console.log('FID:', entry.processingStart - entry.startTime + 'ms');
                });
            });
            observer.observe({ entryTypes: ['first-input'] });
        }
    }

    // Cumulative Layout Shift
    monitorCLS() {
        if ('PerformanceObserver' in window) {
            let clsValue = 0;
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                this.metrics.cls = clsValue;
                console.log('CLS:', clsValue);
            });
            observer.observe({ entryTypes: ['layout-shift'] });
        }
    }

    // First Contentful Paint
    monitorFCP() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    if (entry.name === 'first-contentful-paint') {
                        this.metrics.fcp = entry.startTime;
                        console.log('FCP:', entry.startTime + 'ms');
                    }
                });
            });
            observer.observe({ entryTypes: ['paint'] });
        }
    }

    // Time to First Byte
    monitorTTFB() {
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach((entry) => {
                    if (entry.entryType === 'navigation') {
                        this.metrics.ttfb = entry.responseStart - entry.requestStart;
                        console.log('TTFB:', entry.responseStart - entry.requestStart + 'ms');
                    }
                });
            });
            observer.observe({ entryTypes: ['navigation'] });
        }
    }

    // Monitora metriche custom
    monitorCustomMetrics() {
        // Monitora tempo di caricamento delle animazioni
        this.monitorAnimationPerformance();
        
        // Monitora tempo di risposta degli eventi
        this.monitorEventPerformance();
        
        // Monitora memoria
        this.monitorMemoryUsage();
    }

    // Monitora performance delle animazioni
    monitorAnimationPerformance() {
        const startTime = performance.now();
        
        // Monitora animazioni CSS
        document.addEventListener('animationstart', (e) => {
            const animationStart = performance.now();
            console.log('Animation started:', e.animationName, 'at', animationStart + 'ms');
        });

        document.addEventListener('animationend', (e) => {
            const animationEnd = performance.now();
            console.log('Animation ended:', e.animationName, 'at', animationEnd + 'ms');
        });
    }

    // Monitora performance degli eventi
    monitorEventPerformance() {
        const events = ['click', 'hover', 'focus', 'blur'];
        
        events.forEach(eventType => {
            document.addEventListener(eventType, (e) => {
                const eventTime = performance.now();
                console.log('Event:', eventType, 'at', eventTime + 'ms');
            });
        });
    }

    // Monitora uso memoria
    monitorMemoryUsage() {
        if ('memory' in performance) {
            setInterval(() => {
                const memory = performance.memory;
                this.metrics.memory = {
                    used: memory.usedJSHeapSize,
                    total: memory.totalJSHeapSize,
                    limit: memory.jsHeapSizeLimit
                };
                console.log('Memory usage:', {
                    used: Math.round(memory.usedJSHeapSize / 1024 / 1024) + 'MB',
                    total: Math.round(memory.totalJSHeapSize / 1024 / 1024) + 'MB',
                    limit: Math.round(memory.jsHeapSizeLimit / 1024 / 1024) + 'MB'
                });
            }, 5000);
        }
    }

    // Log performance data
    logPerformanceData() {
        // Log completo dopo 5 secondi
        setTimeout(() => {
            console.log('=== PERFORMANCE REPORT ===');
            console.log('LCP (Largest Contentful Paint):', this.metrics.lcp + 'ms');
            console.log('FID (First Input Delay):', this.metrics.fid + 'ms');
            console.log('CLS (Cumulative Layout Shift):', this.metrics.cls);
            console.log('FCP (First Contentful Paint):', this.metrics.fcp + 'ms');
            console.log('TTFB (Time to First Byte):', this.metrics.ttfb + 'ms');
            console.log('Memory Usage:', this.metrics.memory);
            console.log('==========================');
        }, 5000);
    }

    // Ottieni metriche
    getMetrics() {
        return this.metrics;
    }

    // Invia metriche al server (opzionale)
    sendMetricsToServer() {
        if (Object.keys(this.metrics).length > 0) {
            fetch('/api/performance-metrics/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(this.metrics)
            }).catch(error => {
                console.log('Error sending metrics:', error);
            });
        }
    }
}

// Inizializza performance monitor
document.addEventListener('DOMContentLoaded', function() {
    const performanceMonitor = new PerformanceMonitor();
    
    // Esponi globalmente per debug
    window.performanceMonitor = performanceMonitor;
    
    // Invia metriche dopo 10 secondi
    setTimeout(() => {
        performanceMonitor.sendMetricsToServer();
    }, 10000);
});

// Monitora errori JavaScript
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    console.error('Error details:', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno
    });
});

// Monitora errori di caricamento risorse
window.addEventListener('error', function(e) {
    if (e.target !== window) {
        console.error('Resource loading error:', e.target.src || e.target.href);
    }
}, true);
