# Contribuire a CerCollettiva

Grazie per il tuo interesse a contribuire a CerCollettiva! Questo documento fornisce linee guida per contribuire al progetto in modo efficace.

## 📋 Indice

- [Codice di Condotta](#codice-di-condotta)
- [Come Contribuire](#come-contribuire)
- [Setup Ambiente di Sviluppo](#setup-ambiente-di-sviluppo)
- [Processo di Sviluppo](#processo-di-sviluppo)
- [Standard di Codice](#standard-di-codice)
- [Testing](#testing)
- [Documentazione](#documentazione)
- [Reporting Bug](#reporting-bug)
- [Feature Requests](#feature-requests)
- [Pull Requests](#pull-requests)
- [Release Process](#release-process)

## 🤝 Codice di Condotta

CerCollettiva aderisce al [Codice di Condotta](docs/CODE_OF_CONDUCT.md) per garantire un ambiente inclusivo e rispettoso per tutti i contributori.

### Principi Fondamentali
- **Rispetto**: Tratta tutti con rispetto e cortesia
- **Inclusività**: Benvenuti contributori di ogni background
- **Collaborazione**: Lavora insieme per il bene comune
- **Costruttività**: Feedback costruttivo e positivo

## 🚀 Come Contribuire

### Tipi di Contributi
- **🐛 Bug Fixes**: Correzione di bug esistenti
- **✨ Features**: Nuove funzionalità
- **📚 Documentation**: Miglioramento documentazione
- **🧪 Tests**: Aggiunta o miglioramento test
- **🎨 UI/UX**: Miglioramenti interfaccia utente
- **🔧 DevOps**: Miglioramenti deployment e CI/CD
- **🔒 Security**: Miglioramenti sicurezza
- **🌐 Translation**: Traduzioni e localizzazione

### Prerequisiti
- Conoscenza base di Python e Django
- Familiarità con Git e GitHub
- Ambiente di sviluppo configurato
- Comprensione del dominio CER/CEC (opzionale ma utile)

## 🛠️ Setup Ambiente di Sviluppo

### 1. Fork e Clone
```bash
# Fork del repository su GitHub
# Poi clona il tuo fork
git clone https://github.com/yourusername/CerCollettiva.git
cd CerCollettiva

# Aggiungi upstream remote
git remote add upstream https://github.com/atomozero/CerCollettiva.git
```

### 2. Setup Ambiente
```bash
# Setup automatico
./scripts/setup.sh

# Oppure manuale
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
cp env.example .env
# Modifica .env per sviluppo

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 3. Verifica Setup
```bash
# Test configurazione
python manage.py check

# Avvia server
python manage.py runserver

# Verifica accesso
curl http://127.0.0.1:8000/monitoring/health/
```

## 🔄 Processo di Sviluppo

### 1. Sincronizzazione
```bash
# Aggiorna fork con upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### 2. Creazione Branch
```bash
# Crea branch per feature/bugfix
git checkout -b feature/awesome-feature
# oppure
git checkout -b bugfix/fix-issue-123
```

### 3. Sviluppo
```bash
# Sviluppa la tua feature
# Fai commit frequenti
git add .
git commit -m "feat: add awesome feature"

# Push branch
git push origin feature/awesome-feature
```

### 4. Pull Request
- Crea Pull Request su GitHub
- Segui template PR
- Attendi review e feedback
- Risolvi eventuali conflitti

## 📝 Standard di Codice

### Python Style Guide
- **PEP 8**: Standard Python
- **Black**: Formattazione automatica
- **isort**: Ordinamento import
- **flake8**: Linting

```bash
# Formattazione automatica
black .
isort .

# Linting
flake8 .

# Type checking (opzionale)
mypy .
```

### Django Best Practices
- **DRY**: Don't Repeat Yourself
- **Fat Models, Thin Views**: Logica business nei modelli
- **Generic Views**: Usa Class-Based Views quando possibile
- **Form Validation**: Validazione lato server sempre

### Naming Conventions
```python
# Modelli: PascalCase
class CERConfiguration(models.Model):
    pass

# Funzioni: snake_case
def calculate_energy_consumption():
    pass

# Costanti: UPPER_CASE
MAX_POWER_KW = 1000

# Variabili: snake_case
device_configuration = DeviceConfiguration.objects.get(id=1)
```

### Git Commit Messages
Seguiamo [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new energy calculation algorithm
fix: resolve MQTT connection timeout issue
docs: update API documentation
style: format code with black
refactor: extract common validation logic
test: add unit tests for energy calculator
chore: update dependencies
```

### Tipi di Commit
- **feat**: Nuova funzionalità
- **fix**: Bug fix
- **docs**: Documentazione
- **style**: Formattazione codice
- **refactor**: Refactoring
- **test**: Test
- **chore**: Task di manutenzione

## 🧪 Testing

### Struttura Test
```python
# tests/test_new_feature.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class NewFeatureTestCase(TestCase):
    def setUp(self):
        """Setup test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_feature_functionality(self):
        """Test main functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('new_feature:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Expected Content')
    
    def test_feature_security(self):
        """Test security aspects"""
        response = self.client.get(reverse('new_feature:list'))
        self.assertRedirects(response, '/users/login/?next=/new-feature/')
```

### Esecuzione Test
```bash
# Tutti i test
python manage.py test

# Test specifici
python manage.py test new_feature
python manage.py test new_feature.tests.NewFeatureTestCase

# Con coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Requirements
- **Coverage**: Minimo 80% per nuovo codice
- **Unit Tests**: Ogni funzione pubblica
- **Integration Tests**: Flussi end-to-end
- **Security Tests**: Validazione input, autorizzazione

## 📚 Documentazione

### Tipi di Documentazione
- **Code Comments**: Commenti inline per logica complessa
- **Docstrings**: Documentazione funzioni e classi
- **README**: Setup e uso base
- **API Docs**: Documentazione API REST
- **Architecture**: Documentazione architetturale

### Docstring Format
```python
def calculate_energy_consumption(device_id: str, start_date: datetime, end_date: datetime) -> float:
    """
    Calcola il consumo energetico per un dispositivo in un periodo specifico.
    
    Args:
        device_id (str): ID del dispositivo
        start_date (datetime): Data di inizio periodo
        end_date (datetime): Data di fine periodo
    
    Returns:
        float: Consumo energetico in kWh
    
    Raises:
        DeviceNotFound: Se il dispositivo non esiste
        InvalidDateRange: Se il range di date non è valido
    
    Example:
        >>> consumption = calculate_energy_consumption(
        ...     'device_001', 
        ...     datetime(2024, 1, 1), 
        ...     datetime(2024, 1, 31)
        ... )
        >>> print(f"Consumo: {consumption:.2f} kWh")
    """
    pass
```

### Aggiornamento Documentazione
- Aggiorna documentazione per nuove funzionalità
- Mantieni esempi aggiornati
- Verifica link e riferimenti
- Testa istruzioni di setup

## 🐛 Reporting Bug

### Prima di Segnalare
1. Verifica che il bug non sia già segnalato
2. Testa con l'ultima versione
3. Raccogli informazioni dettagliate

### Template Bug Report
```markdown
## Descrizione Bug
Descrizione chiara e concisa del bug.

## Steps to Reproduce
1. Vai a '...'
2. Clicca su '...'
3. Scorri fino a '...'
4. Vedi errore

## Comportamento Atteso
Descrizione di cosa dovrebbe accadere.

## Screenshots
Se applicabile, aggiungi screenshot.

## Ambiente
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11.0]
- Django: [e.g. 5.0.0]
- Browser: [e.g. Chrome 120]

## Log di Errore
```
Traceback (most recent call last):
  File "...", line ..., in ...
    ...
Error: ...
```

## Informazioni Aggiuntive
Qualsiasi altra informazione rilevante.
```

### Severity Levels
- **Critical**: Sistema non funzionante
- **High**: Funzionalità principale compromessa
- **Medium**: Funzionalità secondaria compromessa
- **Low**: Problema minore o cosmetico

## ✨ Feature Requests

### Prima di Richiedere
1. Verifica che la feature non sia già richiesta
2. Considera se è allineata con gli obiettivi del progetto
3. Valuta l'impatto e la complessità

### Template Feature Request
```markdown
## Descrizione Feature
Descrizione chiara e concisa della feature richiesta.

## Problema da Risolvere
Quale problema risolve questa feature?

## Soluzione Proposta
Descrizione della soluzione proposta.

## Alternative Considerate
Altre soluzioni considerate.

## Use Cases
Casi d'uso specifici per questa feature.

## Mockups/Wireframes
Se applicabile, aggiungi mockups o wireframes.

## Informazioni Aggiuntive
Qualsiasi altra informazione rilevante.
```

### Criteri di Valutazione
- **Alignment**: Allineamento con obiettivi progetto
- **Impact**: Impatto sugli utenti
- **Complexity**: Complessità implementazione
- **Maintenance**: Costi di manutenzione

## 🔀 Pull Requests

### Prima di Creare PR
1. Sincronizza con upstream
2. Crea branch dedicato
3. Implementa feature/fix
4. Aggiungi test
5. Aggiorna documentazione
6. Verifica che tutti i test passino

### Template Pull Request
```markdown
## Descrizione
Breve descrizione delle modifiche.

## Tipo di Modifica
- [ ] Bug fix
- [ ] Nuova feature
- [ ] Breaking change
- [ ] Documentazione
- [ ] Refactoring

## Checklist
- [ ] Codice segue standard del progetto
- [ ] Test aggiunti/aggiornati
- [ ] Documentazione aggiornata
- [ ] Tutti i test passano
- [ ] Codice review completato

## Testing
Descrizione dei test eseguiti.

## Screenshots
Se applicabile, aggiungi screenshot.

## Informazioni Aggiuntive
Qualsiasi altra informazione rilevante.
```

### Processo Review
1. **Automated Checks**: CI/CD pipeline
2. **Code Review**: Almeno 2 approvazioni
3. **Testing**: Verifica funzionalità
4. **Documentation**: Verifica documentazione
5. **Merge**: Merge dopo approvazione

### Criteri di Approvazione
- **Code Quality**: Codice pulito e ben strutturato
- **Testing**: Test appropriati e coverage
- **Documentation**: Documentazione aggiornata
- **Security**: Nessun problema di sicurezza
- **Performance**: Nessun impatto negativo

## 🚀 Release Process

### Versioning
Seguiamo [Semantic Versioning](https://semver.org/):
- **Major (X.0.0)**: Breaking changes
- **Minor (0.X.0)**: New features
- **Patch (0.0.X)**: Bug fixes

### Release Checklist
- [ ] Tutti i test passano
- [ ] Documentazione aggiornata
- [ ] Changelog aggiornato
- [ ] Version bump
- [ ] Tag creato
- [ ] Release notes
- [ ] Deployment testato

### Release Notes
```markdown
## [1.0.0] - 2024-01-01

### Added
- Nuova funzionalità X
- Miglioramento Y

### Changed
- Modifica Z

### Fixed
- Bug fix A
- Bug fix B

### Security
- Fix di sicurezza C
```

## 🏆 Riconoscimenti

### Tipi di Contributori
- **Core Contributors**: Contributori regolari
- **Maintainers**: Mantenitori del progetto
- **Reviewers**: Code reviewers
- **Documenters**: Contributori documentazione
- **Testers**: Beta testers

### Riconoscimenti
- Menzione in CHANGELOG
- Badge GitHub
- Accesso a repository privati
- Invito a eventi community

## 📞 Supporto

### Canali di Supporto
- **GitHub Issues**: Bug e feature requests
- **Discord**: Discussioni e supporto rapido
- **Email**: team@cercollettiva.it

### FAQ
- **Setup Issues**: Vedi [Troubleshooting](TROUBLESHOOTING.md)
- **Development**: Vedi [Developer Guide](docs/DEVELOPER_GUIDE.md)
- **Deployment**: Vedi [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## 📄 Licenza

Contribuendo a CerCollettiva, accetti che le tue modifiche saranno rilasciate sotto la licenza MIT. Vedi [LICENSE](LICENSE) per dettagli.

---

**Grazie per contribuire a CerCollettiva! 🚀**

Insieme stiamo costruendo il futuro dell'energia condivisa e sostenibile.
