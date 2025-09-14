/**
 * Admin Dashboard JavaScript
 * Gestisce i grafici e le interazioni della dashboard amministrativa
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inizializza i grafici
    initEnergyTrendChart();
    initCERDistributionChart();
    
    // Inizializza le animazioni
    initAnimations();
    
    // Inizializza i tooltip
    initTooltips();
});

/**
 * Grafico del trend energetico
 */
function initEnergyTrendChart() {
    const ctx = document.getElementById('energyTrendChart');
    if (!ctx) return;
    
    // Dati di esempio - in produzione verranno passati dal backend
    const energyData = {
        labels: ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'],
        datasets: [
            {
                label: 'Energia Prodotta (kWh)',
                data: [1200, 1350, 1100, 1450, 1300, 1600, 1400],
                borderColor: '#48bb78',
                backgroundColor: 'rgba(72, 187, 120, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Energia Consumata (kWh)',
                data: [800, 900, 750, 950, 850, 1000, 900],
                borderColor: '#4299e1',
                backgroundColor: 'rgba(66, 153, 225, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }
        ]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: energyData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        color: '#718096'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        color: '#718096',
                        callback: function(value) {
                            return value + ' kWh';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Grafico della distribuzione CER
 */
function initCERDistributionChart() {
    const ctx = document.getElementById('cerDistributionChart');
    if (!ctx) return;
    
    // Dati di esempio - in produzione verranno passati dal backend
    const cerData = {
        labels: ['CER Nord', 'CER Centro', 'CER Sud', 'CER Est', 'CER Ovest'],
        datasets: [{
            data: [25, 20, 15, 18, 22],
            backgroundColor: [
                '#4299e1',
                '#48bb78',
                '#ed8936',
                '#9f7aea',
                '#f56565'
            ],
            borderWidth: 0,
            hoverOffset: 10
        }]
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: cerData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} membri (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Inizializza le animazioni
 */
function initAnimations() {
    // Animazione delle stat cards
    const statCards = document.querySelectorAll('.stat-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    statCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease';
        observer.observe(card);
    });
    
    // Animazione dei workflow items
    const workflowItems = document.querySelectorAll('.workflow-item');
    workflowItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        item.style.transition = `all 0.4s ease ${index * 0.1}s`;
        
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
        }, 100 + (index * 100));
    });
}

/**
 * Inizializza i tooltip
 */
function initTooltips() {
    // Tooltip per le stat cards
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Tooltip per i quick action buttons
    const quickActions = document.querySelectorAll('.quick-action-btn');
    quickActions.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.05)';
        });
        
        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/**
 * Aggiorna i dati in tempo reale
 */
function updateDashboardData() {
    // In produzione, questa funzione farà una chiamata AJAX per aggiornare i dati
    console.log('Aggiornamento dati dashboard...');
    
    // Esempio di aggiornamento delle stat cards
    const statValues = document.querySelectorAll('.stat-content h3');
    statValues.forEach(stat => {
        const currentValue = parseInt(stat.textContent);
        const newValue = currentValue + Math.floor(Math.random() * 10);
        stat.textContent = newValue;
        
        // Animazione del cambio valore
        stat.style.transform = 'scale(1.1)';
        setTimeout(() => {
            stat.style.transform = 'scale(1)';
        }, 200);
    });
}

/**
 * Gestisce il refresh automatico
 */
function initAutoRefresh() {
    // Aggiorna i dati ogni 5 minuti
    setInterval(updateDashboardData, 5 * 60 * 1000);
}

/**
 * Gestisce le notifiche in tempo reale
 */
function initRealTimeNotifications() {
    // In produzione, questa funzione si connetterà a WebSocket per notifiche real-time
    console.log('Inizializzazione notifiche real-time...');
    
    // Esempio di notifica
    setTimeout(() => {
        showNotification('Nuovo membro aggiunto alla CER', 'success');
    }, 10000);
}

/**
 * Mostra una notifica
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Stili per la notifica
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#48bb78' : '#4299e1'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 1rem;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    // Rimuovi automaticamente dopo 5 secondi
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Gestisce il tema scuro/chiaro
 */
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Aggiorna i grafici per il nuovo tema
            setTimeout(() => {
                initEnergyTrendChart();
                initCERDistributionChart();
            }, 100);
        });
    }
}

// Inizializza le funzionalità aggiuntive
initAutoRefresh();
initRealTimeNotifications();
initThemeToggle();

// Aggiungi stili CSS per le animazioni
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification {
        animation: slideIn 0.3s ease;
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0;
        margin-left: 1rem;
    }
    
    .notification-close:hover {
        opacity: 0.8;
    }
`;
document.head.appendChild(style);

