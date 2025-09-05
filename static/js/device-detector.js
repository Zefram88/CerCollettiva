/**
 * Device Detector - CerCollettiva
 * Rileva dispositivo e browser per ottimizzazioni specifiche
 */

class DeviceDetector {
    constructor() {
        this.device = this.detectDevice();
        this.browser = this.detectBrowser();
        this.capabilities = this.detectCapabilities();
        this.init();
    }

    detectDevice() {
        const userAgent = navigator.userAgent;
        const platform = navigator.platform;
        
        // Rileva tipo dispositivo
        if (/Android/i.test(userAgent)) {
            return {
                type: 'mobile',
                os: 'android',
                version: this.extractVersion(userAgent, 'Android')
            };
        } else if (/iPhone|iPad|iPod/i.test(userAgent)) {
            return {
                type: /iPad/i.test(userAgent) ? 'tablet' : 'mobile',
                os: 'ios',
                version: this.extractVersion(userAgent, 'OS')
            };
        } else if (/Windows/i.test(platform)) {
            return {
                type: 'desktop',
                os: 'windows',
                version: this.extractVersion(userAgent, 'Windows')
            };
        } else if (/Mac/i.test(platform)) {
            return {
                type: 'desktop',
                os: 'macos',
                version: this.extractVersion(userAgent, 'Mac OS X')
            };
        } else if (/Linux/i.test(platform)) {
            return {
                type: 'desktop',
                os: 'linux',
                version: 'unknown'
            };
        }
        
        return {
            type: 'unknown',
            os: 'unknown',
            version: 'unknown'
        };
    }

    detectBrowser() {
        const userAgent = navigator.userAgent;
        
        if (/Chrome/i.test(userAgent) && !/Edge/i.test(userAgent)) {
            return {
                name: 'chrome',
                version: this.extractVersion(userAgent, 'Chrome')
            };
        } else if (/Firefox/i.test(userAgent)) {
            return {
                name: 'firefox',
                version: this.extractVersion(userAgent, 'Firefox')
            };
        } else if (/Safari/i.test(userAgent) && !/Chrome/i.test(userAgent)) {
            return {
                name: 'safari',
                version: this.extractVersion(userAgent, 'Version')
            };
        } else if (/Edge/i.test(userAgent)) {
            return {
                name: 'edge',
                version: this.extractVersion(userAgent, 'Edge')
            };
        } else if (/Opera/i.test(userAgent)) {
            return {
                name: 'opera',
                version: this.extractVersion(userAgent, 'Opera')
            };
        }
        
        return {
            name: 'unknown',
            version: 'unknown'
        };
    }

    detectCapabilities() {
        return {
            // Touch support
            touch: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
            
            // Hardware acceleration
            hardwareAcceleration: this.testHardwareAcceleration(),
            
            // WebGL support
            webgl: this.testWebGL(),
            
            // CSS Grid support
            cssGrid: CSS.supports('display', 'grid'),
            
            // CSS Flexbox support
            flexbox: CSS.supports('display', 'flex'),
            
            // CSS Custom Properties support
            customProperties: CSS.supports('color', 'var(--test)'),
            
            // Intersection Observer support
            intersectionObserver: 'IntersectionObserver' in window,
            
            // Performance Observer support
            performanceObserver: 'PerformanceObserver' in window,
            
            // Service Worker support
            serviceWorker: 'serviceWorker' in navigator,
            
            // Local Storage support
            localStorage: typeof Storage !== 'undefined',
            
            // IndexedDB support
            indexedDB: 'indexedDB' in window,
            
            // WebRTC support
            webRTC: 'RTCPeerConnection' in window,
            
            // WebSocket support
            webSocket: 'WebSocket' in window,
            
            // Geolocation support
            geolocation: 'geolocation' in navigator,
            
            // Camera support
            camera: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
            
            // Battery API support
            battery: 'getBattery' in navigator,
            
            // Network Information API support
            networkInfo: 'connection' in navigator,
            
            // Device Memory API support
            deviceMemory: 'deviceMemory' in navigator,
            
            // Connection type
            connectionType: navigator.connection ? navigator.connection.effectiveType : 'unknown',
            
            // Screen dimensions
            screen: {
                width: screen.width,
                height: screen.height,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            },
            
            // Viewport dimensions
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            
            // Device pixel ratio
            pixelRatio: window.devicePixelRatio || 1,
            
            // Orientation
            orientation: screen.orientation ? screen.orientation.type : 'unknown',
            
            // Language
            language: navigator.language,
            languages: navigator.languages
        };
    }

    testHardwareAcceleration() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        return !!gl;
    }

    testWebGL() {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        return !!gl;
    }

    extractVersion(userAgent, keyword) {
        const regex = new RegExp(keyword + '/([0-9.]+)', 'i');
        const match = userAgent.match(regex);
        return match ? match[1] : 'unknown';
    }

    init() {
        // Applica ottimizzazioni specifiche per dispositivo
        this.applyDeviceOptimizations();
        
        // Log informazioni dispositivo
        this.logDeviceInfo();
        
        // Monitora cambiamenti
        this.monitorChanges();
    }

    applyDeviceOptimizations() {
        const body = document.body;
        
        // Aggiungi classi CSS per dispositivo
        body.classList.add(`device-${this.device.type}`);
        body.classList.add(`os-${this.device.os}`);
        body.classList.add(`browser-${this.browser.name}`);
        
        // Ottimizzazioni per touch devices
        if (this.capabilities.touch) {
            body.classList.add('touch-device');
            
            // Riduci effetti hover su touch devices
            const style = document.createElement('style');
            style.textContent = `
                .touch-device .cer-card:hover {
                    transform: translateY(-2px) scale(1.01);
                }
                .touch-device .btn-cer-primary:hover {
                    transform: translateY(-2px) scale(1.03);
                }
            `;
            document.head.appendChild(style);
        }
        
        // Ottimizzazioni per dispositivi con bassa memoria
        if (this.capabilities.deviceMemory && this.capabilities.deviceMemory < 4) {
            body.classList.add('low-memory-device');
            
            // Riduci animazioni su dispositivi con poca memoria
            const style = document.createElement('style');
            style.textContent = `
                .low-memory-device .cer-card,
                .low-memory-device .btn-cer-primary,
                .low-memory-device .search-form-container .form-control {
                    transition: none;
                    animation: none;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Ottimizzazioni per connessioni lente
        if (this.capabilities.connectionType === 'slow-2g' || this.capabilities.connectionType === '2g') {
            body.classList.add('slow-connection');
            
            // Riduci animazioni su connessioni lente
            const style = document.createElement('style');
            style.textContent = `
                .slow-connection .cer-card,
                .slow-connection .btn-cer-primary,
                .slow-connection .search-form-container .form-control {
                    transition: none;
                    animation: none;
                }
            `;
            document.head.appendChild(style);
        }
    }

    logDeviceInfo() {
        console.log('=== DEVICE DETECTION ===');
        console.log('Device:', this.device);
        console.log('Browser:', this.browser);
        console.log('Capabilities:', this.capabilities);
        console.log('========================');
    }

    monitorChanges() {
        // Monitora cambiamenti orientamento
        if (screen.orientation) {
            screen.orientation.addEventListener('change', () => {
                this.capabilities.orientation = screen.orientation.type;
                console.log('Orientation changed:', screen.orientation.type);
            });
        }
        
        // Monitora cambiamenti viewport
        window.addEventListener('resize', () => {
            this.capabilities.viewport = {
                width: window.innerWidth,
                height: window.innerHeight
            };
            console.log('Viewport changed:', this.capabilities.viewport);
        });
        
        // Monitora cambiamenti connessione
        if (navigator.connection) {
            navigator.connection.addEventListener('change', () => {
                this.capabilities.connectionType = navigator.connection.effectiveType;
                console.log('Connection changed:', navigator.connection.effectiveType);
            });
        }
    }

    // Ottieni informazioni dispositivo
    getDeviceInfo() {
        return {
            device: this.device,
            browser: this.browser,
            capabilities: this.capabilities
        };
    }

    // Invia informazioni al server (opzionale)
    sendDeviceInfoToServer() {
        const deviceInfo = this.getDeviceInfo();
        
        fetch('/api/device-info/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(deviceInfo)
        }).catch(error => {
            console.log('Error sending device info:', error);
        });
    }
}

// Inizializza device detector
document.addEventListener('DOMContentLoaded', function() {
    const deviceDetector = new DeviceDetector();
    
    // Esponi globalmente per debug
    window.deviceDetector = deviceDetector;
    
    // Invia informazioni dopo 5 secondi
    setTimeout(() => {
        deviceDetector.sendDeviceInfoToServer();
    }, 5000);
});
