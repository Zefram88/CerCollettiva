#core\models.py
import re, uuid, time, logging
import paho.mqtt.client as mqtt
#from energy.models import DeviceMeasurement, DeviceConfiguration
from paho.mqtt.client import CallbackAPIVersion
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
logger = logging.getLogger(__name__)

def generate_mqtt_client_id():
    """Genera un ID client MQTT univoco"""
    import uuid
    return f"cercollettiva-{str(uuid.uuid4())}"

class CERConfiguration(models.Model):
    """Configurazione di una Comunità Energetica Rinnovabile"""
    name = models.CharField("Nome", max_length=255)
    code = models.CharField("Codice identificativo", max_length=50, unique=True)
    primary_substation = models.CharField("Cabina primaria", max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField("Attiva", default=True)
    
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CERMembership',
        through_fields=('cer_configuration', 'user'),
        related_name='cer_configurations'
    )

    class Meta:
        verbose_name = "Configurazione CER"
        verbose_name_plural = "Configurazioni CER"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"

class CERDistributionConfiguration(models.Model):
    """Configurazione della ripartizione economica della CER"""
    cer_configuration = models.OneToOneField(
        CERConfiguration,
        on_delete=models.CASCADE,
        related_name='distribution_config',
        verbose_name="Configurazione CER"
    )
    
    # Percentuali di ripartizione
    producer_percentage = models.DecimalField(
        "Percentuale Produttori (%)",
        max_digits=5,
        decimal_places=2,
        default=45.00,
        help_text="Percentuale destinata ai produttori"
    )
    consumer_percentage = models.DecimalField(
        "Percentuale Consumatori (%)", 
        max_digits=5,
        decimal_places=2,
        default=30.00,
        help_text="Percentuale destinata ai consumatori"
    )
    management_percentage = models.DecimalField(
        "Percentuale Gestione (%)",
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="Percentuale per spese di gestione (commercialista, spese vive, bancarie, legali, marketing)"
    )
    investment_fund_percentage = models.DecimalField(
        "Percentuale Fondo Investimento (%)",
        max_digits=5,
        decimal_places=2,
        default=3.00,
        help_text="Percentuale per fondo investimenti"
    )
    solidarity_fund_percentage = models.DecimalField(
        "Percentuale Fondo Solidarietà (%)",
        max_digits=5,
        decimal_places=2,
        default=2.00,
        help_text="Percentuale per fondo di solidarietà"
    )
    
    # Metadati
    created_at = models.DateTimeField("Creato il", auto_now_add=True)
    updated_at = models.DateTimeField("Aggiornato il", auto_now=True)
    is_active = models.BooleanField("Configurazione Attiva", default=True)
    
    # Note descrittive per trasparenza
    management_description = models.TextField(
        "Descrizione Spese Gestione",
        blank=True,
        help_text="Dettaglio delle spese coperte dalla percentuale di gestione"
    )
    investment_description = models.TextField(
        "Descrizione Fondo Investimento",
        blank=True,
        help_text="Descrizione degli investimenti pianificati"
    )
    solidarity_description = models.TextField(
        "Descrizione Fondo Solidarietà", 
        blank=True,
        help_text="Criteri e finalità del fondo di solidarietà"
    )
    
    def clean(self):
        """Validazione che la somma delle percentuali sia 100%"""
        total_percentage = (
            self.producer_percentage + 
            self.consumer_percentage +
            self.management_percentage +
            self.investment_fund_percentage +
            self.solidarity_fund_percentage
        )
        
        if abs(total_percentage - 100) > 0.01:  # Tolleranza per arrotondamenti
            raise ValidationError(
                f"La somma delle percentuali deve essere 100%. Attuale: {total_percentage}%"
            )
    
    def get_distribution_breakdown(self, total_amount):
        """Calcola la ripartizione dell'importo totale secondo le percentuali configurate"""
        return {
            'producers': round(total_amount * (self.producer_percentage / 100), 2),
            'consumers': round(total_amount * (self.consumer_percentage / 100), 2),
            'management': round(total_amount * (self.management_percentage / 100), 2),
            'investment_fund': round(total_amount * (self.investment_fund_percentage / 100), 2),
            'solidarity_fund': round(total_amount * (self.solidarity_fund_percentage / 100), 2),
            'total': total_amount
        }
    
    @property 
    def total_percentage(self):
        """Calcola la percentuale totale configurata"""
        return (
            self.producer_percentage + 
            self.consumer_percentage +
            self.management_percentage +
            self.investment_fund_percentage +
            self.solidarity_fund_percentage
        )
    
    class Meta:
        verbose_name = "Configurazione Ripartizione Economica CER"
        verbose_name_plural = "Configurazioni Ripartizione Economica CER"
    
    def __str__(self):
        return f"Ripartizione {self.cer_configuration.name} - P:{self.producer_percentage}% C:{self.consumer_percentage}% G:{self.management_percentage}%"

class GSEIncomeTracking(models.Model):
    """Tracciamento degli incassi GSE per una CER"""
    
    PAYMENT_TYPES = [
        ('ADVANCE', 'Acconto Mensile'),
        ('SETTLEMENT', 'Conguaglio Finale'),
        ('ADJUSTMENT', 'Rettifica'),
    ]
    
    PAYMENT_STATUS = [
        ('EXPECTED', 'Atteso'),
        ('RECEIVED', 'Ricevuto'),
        ('DELAYED', 'In Ritardo'), 
        ('DISPUTED', 'Contestato'),
    ]
    
    cer_configuration = models.ForeignKey(
        CERConfiguration,
        on_delete=models.CASCADE,
        related_name='gse_incomes',
        verbose_name="Configurazione CER"
    )
    
    # Informazioni pagamento
    payment_type = models.CharField(
        "Tipo Pagamento",
        max_length=20,
        choices=PAYMENT_TYPES
    )
    reference_month = models.DateField(
        "Mese di Riferimento",
        help_text="Mese a cui si riferisce il pagamento"
    )
    reference_year = models.IntegerField(
        "Anno di Riferimento",
        help_text="Anno a cui si riferisce il pagamento"
    )
    
    # Importi
    gross_amount = models.DecimalField(
        "Importo Lordo GSE (€)",
        max_digits=12,
        decimal_places=2,
        help_text="Importo lordo ricevuto dal GSE"
    )
    net_amount = models.DecimalField(
        "Importo Netto (€)",
        max_digits=12,
        decimal_places=2,
        help_text="Importo netto dopo detrazioni"
    )
    taxes_amount = models.DecimalField(
        "Imposte e Detrazioni (€)",
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Imposte, contributi e altre detrazioni"
    )
    
    # Date e stato
    expected_payment_date = models.DateField(
        "Data Attesa Pagamento",
        null=True,
        blank=True
    )
    actual_payment_date = models.DateField(
        "Data Pagamento Effettivo",
        null=True,
        blank=True
    )
    payment_status = models.CharField(
        "Stato Pagamento",
        max_length=20,
        choices=PAYMENT_STATUS,
        default='EXPECTED'
    )
    
    # Dettagli tecnici GSE
    gse_practice_number = models.CharField(
        "Numero Pratica GSE",
        max_length=50,
        blank=True,
        help_text="Numero identificativo della pratica GSE"
    )
    shared_energy_kwh = models.DecimalField(
        "Energia Condivisa (kWh)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="kWh di energia condivisa nel periodo"
    )
    energy_tariff = models.DecimalField(
        "Tariffa Energia (€/kWh)", 
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Tariffa applicata per l'energia condivisa"
    )
    
    # Note e allegati
    notes = models.TextField(
        "Note",
        blank=True,
        help_text="Note aggiuntive sul pagamento"
    )
    gse_communication = models.FileField(
        "Comunicazione GSE",
        upload_to='gse/communications/%Y/%m/',
        null=True,
        blank=True,
        help_text="File della comunicazione GSE"
    )
    
    # Metadati
    created_at = models.DateTimeField("Creato il", auto_now_add=True)
    updated_at = models.DateTimeField("Aggiornato il", auto_now=True)
    
    def clean(self):
        """Validazioni custom per il modello"""
        if self.gross_amount and self.net_amount and self.taxes_amount:
            calculated_net = self.gross_amount - self.taxes_amount
            if abs(calculated_net - self.net_amount) > 0.01:
                raise ValidationError(
                    f"L'importo netto ({self.net_amount}) non corrisponde al calcolo "
                    f"lordo - imposte ({calculated_net})"
                )
    
    def calculate_distribution(self):
        """Calcola la ripartizione secondo la configurazione della CER"""
        try:
            distribution_config = self.cer_configuration.distribution_config
            return distribution_config.get_distribution_breakdown(float(self.net_amount))
        except CERDistributionConfiguration.DoesNotExist:
            return None
    
    @property
    def is_overdue(self):
        """Verifica se il pagamento è in ritardo"""
        if not self.expected_payment_date or self.payment_status == 'RECEIVED':
            return False
        return timezone.now().date() > self.expected_payment_date
    
    @property
    def days_overdue(self):
        """Calcola i giorni di ritardo"""
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.expected_payment_date).days
    
    def mark_as_received(self, actual_date=None):
        """Marca il pagamento come ricevuto"""
        self.payment_status = 'RECEIVED'
        self.actual_payment_date = actual_date or timezone.now().date()
        self.save(update_fields=['payment_status', 'actual_payment_date', 'updated_at'])
    
    class Meta:
        verbose_name = "Tracciamento Incassi GSE"
        verbose_name_plural = "Tracciamento Incassi GSE"
        unique_together = ['cer_configuration', 'payment_type', 'reference_month', 'reference_year']
        ordering = ['-reference_year', '-reference_month', '-created_at']
        indexes = [
            models.Index(fields=['cer_configuration', '-reference_year', '-reference_month']),
            models.Index(fields=['payment_status', 'expected_payment_date']),
        ]
    
    def __str__(self):
        return f"{self.cer_configuration.name} - {self.get_payment_type_display()} {self.reference_month.strftime('%m/%Y')} - €{self.net_amount}"

class CERMembership(models.Model):
    """Associazione tra Utente e CER con gestione documenti GDPR"""
    ROLE_CHOICES = [
        ('ADMIN', 'Amministratore'),
        ('MEMBER', 'Membro'),
        ('TECHNICAL', 'Tecnico'),
    ]
    
    MEMBER_TYPE_CHOICES = [
        ('PRODUCER', 'Produttore'),
        ('CONSUMER', 'Solo Consumatore'),
        ('PROSUMER', 'Prosumer'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cer_memberships'
    )
    cer_configuration = models.ForeignKey(
        CERConfiguration,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        "Ruolo",
        max_length=20,
        choices=ROLE_CHOICES,
        default='MEMBER'
    )
    member_type = models.CharField(
        "Tipologia Membro",
        max_length=20,
        choices=MEMBER_TYPE_CHOICES,
        default='CONSUMER',
        help_text="Tipo di partecipazione nella CER"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField("Attivo", default=True)

    # Documenti con protezione GDPR
    conformity_declaration = models.FileField(
        "Dichiarazione di conformità",
        upload_to='cer/conformity/%Y/%m/%d/',
        null=True,
        blank=True
    )
    gse_practice = models.FileField(
        "Pratica GSE",
        upload_to='cer/gse/%Y/%m/%d/',
        null=True,
        blank=True
    )
    panels_photo = models.FileField(
        "Foto pannelli",
        upload_to='cer/panels/%Y/%m/%d/',
        null=True,
        blank=True
    )
    inverter_photo = models.FileField(
        "Foto inverter",
        upload_to='cer/inverter/%Y/%m/%d/',
        null=True,
        blank=True
    )
    panels_serial_list = models.TextField(
        "Lista seriali pannelli",
        blank=True,
        null=True
    )
    
    # Verifica documenti con audit trail
    document_verified = models.BooleanField("Documenti verificati", default=False)
    document_verified_at = models.DateTimeField(null=True, blank=True)
    document_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_memberships'
    )

    @property
    def is_producer(self):
        """Verifica se il membro è un produttore"""
        return self.member_type in ['PRODUCER', 'PROSUMER']
    
    @property 
    def is_consumer(self):
        """Verifica se il membro è un consumatore"""
        return self.member_type in ['CONSUMER', 'PROSUMER']
    
    @property
    def requires_production_documents(self):
        """Verifica se il membro richiede documenti di produzione"""
        return self.member_type in ['PRODUCER', 'PROSUMER']
    
    def auto_approve_consumer(self):
        """Approvazione automatica per soli consumatori"""
        if self.member_type == 'CONSUMER':
            self.document_verified = True
            self.document_verified_at = timezone.now()
            self.save(update_fields=['document_verified', 'document_verified_at'])
            return True
        return False
    
    def create_membership_card(self):
        """Crea la tessera associativa per il membro"""
        if hasattr(self, 'card'):
            return self.card  # Tessera già esistente
            
        from datetime import timedelta
        
        card = MembershipCard(
            membership=self,
            expiry_date=timezone.now() + timedelta(days=365)  # 1 anno
        )
        card.generate_card_number()
        card.save()
        return card
    
    def register_in_registry(self):
        """Registra il membro nel registro soci"""
        if hasattr(self, 'registry_entry') and self.registry_entry.exists():
            return self.registry_entry.first()  # Già registrato
            
        return MemberRegistry.register_member(self)
    
    def complete_membership_setup(self):
        """Completa la configurazione della membership con tessera e registrazione"""
        card = self.create_membership_card()
        registry = self.register_in_registry()
        return card, registry

    class Meta:
        verbose_name = "Membership CER"
        verbose_name_plural = "Membership CER"
        unique_together = ['user', 'cer_configuration']

    def __str__(self):
        return f"{self.user.username} - {self.cer_configuration.name} ({self.get_member_type_display()})"

class MembershipCard(models.Model):
    """Tessera associativa per membri CER"""
    membership = models.OneToOneField(
        CERMembership, 
        on_delete=models.CASCADE, 
        related_name='card'
    )
    card_number = models.CharField(
        "Numero Tessera",
        max_length=20, 
        unique=True,
        help_text="Numero identificativo univoco della tessera"
    )
    issue_date = models.DateTimeField(
        "Data Emissione",
        auto_now_add=True
    )
    expiry_date = models.DateTimeField(
        "Data Scadenza",
        help_text="Data di scadenza della tessera"
    )
    is_active = models.BooleanField(
        "Attiva",
        default=True
    )
    
    # Campi per gestione quote associative
    membership_fee_paid = models.BooleanField(
        "Quota Pagata",
        default=False
    )
    fee_payment_date = models.DateTimeField(
        "Data Pagamento Quota",
        null=True, 
        blank=True
    )
    fee_amount = models.DecimalField(
        "Importo Quota",
        max_digits=8, 
        decimal_places=2, 
        default=0,
        help_text="Quota associativa in euro"
    )
    payment_method = models.CharField(
        "Metodo Pagamento",
        max_length=50,
        choices=[
            ('CASH', 'Contanti'),
            ('BANK_TRANSFER', 'Bonifico'),
            ('CARD', 'Carta'),
            ('OTHER', 'Altro')
        ],
        blank=True
    )
    
    @property
    def is_expired(self):
        """Verifica se la tessera è scaduta"""
        return timezone.now() > self.expiry_date
    
    @property
    def is_valid(self):
        """Verifica se la tessera è valida"""
        return self.is_active and not self.is_expired and self.membership.is_active
    
    def generate_card_number(self):
        """Genera automaticamente il numero tessera"""
        cer_code = self.membership.cer_configuration.code
        year = timezone.now().year
        # Conta i membri esistenti per questa CER
        member_count = MembershipCard.objects.filter(
            membership__cer_configuration=self.membership.cer_configuration
        ).count() + 1
        
        self.card_number = f"{cer_code}-{year}-{member_count:04d}"
    
    def renew(self, months=12):
        """Rinnova la tessera per il numero di mesi specificato"""
        from datetime import timedelta
        self.expiry_date = timezone.now() + timedelta(days=months*30)
        self.is_active = True
        self.save()
    
    def pay_fee(self, amount, payment_method='BANK_TRANSFER'):
        """Registra il pagamento della quota associativa"""
        self.fee_amount = amount
        self.payment_method = payment_method
        self.membership_fee_paid = True
        self.fee_payment_date = timezone.now()
        self.save()

    class Meta:
        verbose_name = "Tessera Associativa"
        verbose_name_plural = "Tessere Associative"
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['card_number']),
            models.Index(fields=['is_active', 'expiry_date']),
        ]

    def __str__(self):
        return f"Tessera {self.card_number} - {self.membership.user.username}"

class MemberRegistry(models.Model):
    """Registro progressivo dei soci per CER"""
    cer_configuration = models.ForeignKey(
        CERConfiguration, 
        on_delete=models.CASCADE,
        related_name='member_registry'
    )
    progressive_number = models.PositiveIntegerField(
        "Numero Progressivo"
    )
    membership = models.ForeignKey(
        CERMembership, 
        on_delete=models.CASCADE,
        related_name='registry_entry'
    )
    registration_date = models.DateTimeField(
        "Data Registrazione",
        auto_now_add=True
    )
    notes = models.TextField(
        "Note",
        blank=True,
        help_text="Note aggiuntive sulla registrazione"
    )
    
    @classmethod
    def register_member(cls, membership):
        """Registra un membro nel registro con numero progressivo automatico"""
        last_entry = cls.objects.filter(
            cer_configuration=membership.cer_configuration
        ).order_by('-progressive_number').first()
        
        next_number = 1 if not last_entry else last_entry.progressive_number + 1
        
        return cls.objects.create(
            cer_configuration=membership.cer_configuration,
            membership=membership,
            progressive_number=next_number
        )

    class Meta:
        verbose_name = "Registro Soci"
        verbose_name_plural = "Registro Soci"
        unique_together = ['cer_configuration', 'progressive_number']
        ordering = ['cer_configuration', 'progressive_number']
        indexes = [
            models.Index(fields=['cer_configuration', 'progressive_number']),
        ]

    def __str__(self):
        return f"{self.cer_configuration.code} - {self.progressive_number:04d} - {self.membership.user.username}"

class Plant(models.Model):
    """Impianto energetico con supporto MQTT"""
    PLANT_TYPES = [
        ('CONSUMER', 'Consumatore'),
        ('PRODUCER', 'Produttore'),
        ('PROSUMER', 'Prosumer'),
    ]
    
    raw_address = models.TextField(
        "Indirizzo grezzo",
        blank=True,
        null=True,
        help_text="Indirizzo originale non processato dall'attestato Gaudì"
    )
    # Identificazione impianto
    name = models.CharField("Nome impianto", max_length=255)
    pod_code = models.CharField("Codice POD", max_length=50, unique=True)
    plant_type = models.CharField("Tipologia", max_length=20, choices=PLANT_TYPES)

    # Associazione
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='plants')
    cer_configuration = models.ForeignKey('CERConfiguration', on_delete=models.SET_NULL, null=True, blank=True, related_name='plants')


    # Dati tecnici
    nominal_power = models.FloatField("Potenza nominale (kW)")
    connection_voltage = models.CharField("Tensione connessione", max_length=50)
    installation_date = models.DateField("Data installazione")
    
    # Indirizzo
    address = models.CharField("Indirizzo", max_length=255)
    city = models.CharField("Città", max_length=100)
    zip_code = models.CharField("CAP", max_length=5)
    province = models.CharField("Provincia", max_length=2)
    latitude = models.DecimalField("Latitudine", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Longitudine", max_digits=9, decimal_places=6, null=True, blank=True)


    # Stato
    is_active = models.BooleanField("Attivo", default=True)
    mqtt_connected = models.BooleanField("Connesso MQTT", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Dati Gaudì
    gaudi_request_code = models.CharField("Codice richiesta Gaudì", max_length=50, blank=True, null=True)
    censimp_code = models.CharField("Codice CENSIMP", max_length=50, blank=True, null=True)

    sapr_code = models.CharField(
        "Codice SAPR",
        max_length=50,
        blank=True,
        null=True,
        help_text="Codice SAPR nell'attestazione Gaudì"
    )
    validation_date = models.DateField(
        "Data Convalida Gaudì",
        null=True,
        blank=True,
        help_text="Data di convalida dell'attestazione Gaudì"
    )
    gaudi_voltage = models.IntegerField(
        "Tensione Gaudì",
        null=True,
        blank=True,
        help_text="Tensione di generazione dichiarata in Gaudì (V)"
    )
    expected_yearly_production = models.IntegerField(
        "Produzione Annua Attesa",
        null=True,
        blank=True,
        help_text="Produzione lorda media annua attesa in kWh"
    )
    expected_operation_date = models.DateField(
        "Data Presunto Esercizio",
        null=True,
        blank=True,
        help_text="Data di presunto esercizio dichiarata in Gaudì"
    )
    gaudi_verified = models.BooleanField("Verificato Gaudì", default=False, help_text="Indica se i dati sono stati verificati con attestazione Gaudì")
    gaudi_verification_date = models.DateTimeField("Data verifica Gaudì", null=True, blank=True, help_text="Data in cui è stato verificato l'attestato Gaudì")
    gaudi_version = models.IntegerField(
        "Versione Gaudì",
        null=True,
        blank=True,
        help_text="Numero versione dell'attestato Gaudì"
    )

    # Dati tecnici aggiuntivi da Gaudì
    section_type = models.CharField(
        "Tipo Sezione",
        max_length=50,
        blank=True,
        null=True,
        help_text="Tipo di sezione dell'impianto (es. SILICIO MONOCRISTALLINO)"
    )
    section_id = models.CharField(
        "ID Sezione CENSIMP",
        max_length=50,
        blank=True,
        null=True,
        help_text="Identificativo della sezione nel sistema CENSIMP"
    )
    group_id = models.CharField(
        "ID Gruppo CENSIMP",
        max_length=50,
        blank=True,
        null=True,
        help_text="Identificativo del gruppo nel sistema CENSIMP"
    )
    generator_group_id = models.CharField(
        "Numero Gruppo",
        max_length=50,
        blank=True,
        null=True,
        help_text="Numero identificativo del gruppo generatore"
    )
    remote_disconnect = models.BooleanField(
        "Teledistacco",
        default=False,
        help_text="Indica se l'impianto è predisposto per il teledistacco"
    )
    active_power = models.FloatField(
        "Potenza Attiva Nominale",
        null=True,
        blank=True,
        help_text="Potenza attiva nominale del generatore (kW)"
    )
    net_power = models.FloatField(
        "Potenza Efficiente Netta",
        null=True,
        blank=True,
        help_text="Potenza efficiente netta dell'impianto (kW)"
    )
    gross_power = models.FloatField(
        "Potenza Efficiente Lorda",
        null=True,
        blank=True,
        help_text="Potenza efficiente lorda dell'impianto (kW)"
    )
    grid_feed_type = models.CharField(
        "Tipo Immissione",
        max_length=10,
        choices=[('TOTAL', 'Totale'), ('PARTIAL', 'Parziale')],
        default='TOTAL',
        help_text="Tipo di immissione in rete"
    )
    has_storage = models.BooleanField(
        "Sistema Accumulo",
        default=False,
        help_text="Indica se l'impianto dispone di un sistema di accumulo"
    )
    gaudi_certificate_uploaded = models.BooleanField(
        default=False,
        verbose_name="Attestato GAUDÌ caricato"
    )
    gaudi_upload_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Data caricamento GAUDÌ"
    )

    # Configurazione MQTT sicura
    mqtt_broker = models.CharField(max_length=255, null=True, blank=True)
    mqtt_port = models.IntegerField(default=1883)
    mqtt_username = models.CharField(max_length=255, null=True, blank=True)
    mqtt_password = models.CharField(max_length=255, null=True, blank=True)
    mqtt_topic_prefix = models.CharField(
        "MQTT Topic Prefix",
        max_length=255,
        default='cercollettiva/',
        help_text="Prefisso per i topic MQTT (es. cercollettiva/pod_code)"
    )
    mqtt_client_id = models.CharField(
        "MQTT Client ID",
        max_length=255,
        unique=True,
        default=generate_mqtt_client_id,
        help_text="Identificativo univoco per il client MQTT"
    )
    use_ssl = models.BooleanField("Usa SSL/TLS", default=True)

    def set_gaudi_verification(self, verification_data=None):
        """Sets Gaudì verification status with proper validation"""
        self.gaudi_verified = True
        self.gaudi_verification_date = timezone.now()
        if verification_data:
            # Process additional verification data
            pass
        self.save(update_fields=['gaudi_verified', 'gaudi_verification_date'])

    def verify_gaudi(self, document=None, verification_data=None):
            try:
                if self.gaudi_verified:
                    logger.warning(f"Impianto {self.id} già verificato Gaudì in data {self.gaudi_verification_date}")
                    return False
                self.gaudi_verified = True
                self.gaudi_verification_date = timezone.now()
                if verification_data:
                    for field, value in verification_data.items():
                        if hasattr(self, field):
                            setattr(self, field, value)
                        else:
                            logger.warning(f"Campo {field} non presente nel modello Plant")
                if document:
                    document.type = 'GAUDI'
                    document.plant = self
                    try:
                        document.save()
                        logger.info(f"Documento Gaudì (ID: {document.id}) associato all'impianto {self.id}")
                    except Exception as e:
                        logger.error(f"Errore nel salvare il documento Gaudì: {str(e)}")
                        raise ValidationError("Impossibile salvare il documento Gaudì")
                self.save()
                logger.info(f"Impianto {self.id} verificato Gaudì con successo in data {self.gaudi_verification_date}")
                return True
            except Exception as e:
                logger.error(f"Errore durante la verifica Gaudì dell'impianto {self.id}: {str(e)}")
                raise ValidationError(f"Errore durante la verifica Gaudì: {str(e)}")

    def has_valid_gaudi(self):
            return bool(self.gaudi_verified and self.gaudi_verification_date and self.gaudi_request_code)

    class Meta:
        verbose_name = "Impianto"
        verbose_name_plural = "Impianti"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.name} - {self.pod_code}"

    def get_full_address(self):
            """Restituisce l'indirizzo completo per il geocoding"""
            return f"{self.address}, {self.zip_code} {self.city} {self.province}, Italy"

    def geocode_address(self, retry_count=3):
        """Ottiene le coordinate geografiche dall'indirizzo"""
        if not self.address:
            logger.warning("[GEOCODING] Indirizzo mancante")
            return False

        geolocator = Nominatim(user_agent="cercollettiva")
        geolocator.timeout = 10

        try:
            search_address = f"{self.address}, {self.city}, {self.province}, Italy"
            logger.info(f"[GEOCODING] Searching: '{search_address}'")
                
            location = geolocator.geocode(search_address, exactly_one=True)
            
            if location:
                logger.info(f"[GEOCODING] Found: {location.address}")
                logger.info(f"[GEOCODING] Coordinates: {location.latitude}, {location.longitude}")
                
                self.latitude = location.latitude
                self.longitude = location.longitude
                return True
                
            logger.warning("[GEOCODING] No results found")
            return False
                    
        except Exception as e:
            logger.error(f"[GEOCODING] Error: {str(e)}")
            return False

    def clean(self):
        """Validazione custom per l'impianto"""
        if self.cer_configuration:
            membership = CERMembership.objects.filter(
                user=self.owner,
                cer_configuration=self.cer_configuration,
                is_active=True
            ).exists()
            
            if not membership:
                raise ValidationError(
                    _("Il proprietario dell'impianto deve essere membro attivo della CER")
                )

        if self.gaudi_verified:
            self.validate_gaudi_data()

    def test_mqtt_connection(self):
        """Test the MQTT connection for this plant"""
        try:
            client = mqtt.Client(
                client_id=self.mqtt_client_id,
                protocol=mqtt.MQTTv5,
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2
            )
            
            # Configura le credenziali se necessario
            if self.mqtt_username or (hasattr(settings, 'MQTT_USERNAME') and settings.MQTT_USERNAME):
                username = self.mqtt_username or settings.MQTT_USERNAME
                password = self.mqtt_password or settings.MQTT_PASSWORD
                client.username_pw_set(username, password)

            # Variabile per tracciare lo stato della connessione
            connection_status = {'connected': False}

            def on_connect(client, userdata, flags, rc, properties):
                connection_status['connected'] = (rc == 0)
                client.disconnect()

            client.on_connect = on_connect

            # Tenta la connessione
            try:
                broker = self.mqtt_broker or settings.MQTT_BROKER
                port = self.mqtt_port or settings.MQTT_PORT
                
                client.connect(
                    host=broker,
                    port=port,
                    keepalive=60
                )
                client.loop_start()
                time.sleep(1)  # Breve attesa per permettere la connessione
                client.loop_stop()
                
                # Aggiorna lo stato della connessione nel modello
                self.mqtt_connected = connection_status['connected']
                self.save(update_fields=['mqtt_connected'])
                
                return self.mqtt_connected
                
            except Exception as e:
                self.mqtt_connected = False
                self.save(update_fields=['mqtt_connected'])
                return False
            finally:
                try:
                    client.disconnect()
                except:
                    pass

        except Exception as e:
            self.mqtt_connected = False
            self.save(update_fields=['mqtt_connected'])
            return False

    def check_mqtt_connection(self):
        """Check if MQTT connection is available"""
        try:
            return self.test_mqtt_connection()
        except Exception:
            return False
        
    def save(self, *args, **kwargs):
        # Flag per evitare ricorsione infinita
        do_geocoding = kwargs.pop('do_geocoding', True)
        
        # Imposta il topic MQTT come prima
        if not self.mqtt_topic_prefix and self.pod_code:
            self.mqtt_topic_prefix = f"cercollettiva/{self.pod_code}"

        # Prima salva l'oggetto per assicurarsi di avere un ID
        super().save(*args, **kwargs)

        # Verifica se è necessario aggiornare le coordinate
        if do_geocoding and (not self.latitude or not self.longitude):
            if self.geocode_address():
                # Salva solo se il geocoding ha successo
                # Non passiamo do_geocoding a super().save()
                super().save(update_fields=['latitude', 'longitude'])
                
    def get_energy_today(self):
        """Calcola l'energia totale prodotta oggi."""
        today = timezone.now().date()
        return self.mqtt_data.filter(
            variable_type__contains='ENERGY',
            timestamp__date=today
        ).order_by('-timestamp').first()

    def get_current_power(self):
        """Ottiene l'ultima lettura di potenza."""
        return self.mqtt_data.filter(
            variable_type__contains='POWER'
        ).order_by('-timestamp').first()

    def get_max_power_today(self):
        """Calcola la potenza massima del giorno."""
        today = timezone.now().date()
        return self.mqtt_data.filter(
            variable_type__contains='POWER',
            timestamp__date=today
        ).aggregate(max_power=models.Max('value'))['max_power'] or 0

    def get_daily_energy_data(self, days=7):
        """Recupera i dati di energia degli ultimi giorni."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
    
        return self.mqtt_data.filter(
            variable_type__contains='ENERGY',
            timestamp__date__gte=start_date
        ).annotate(
            date=models.functions.TruncDate('timestamp')
        ).values('date').annotate(
            energy=models.Max('value')
        ).order_by('date')

    def verify_gaudi_data(self, attestation_data):
        """
        Verifica e aggiorna i dati dell'impianto con quelli dell'attestazione Gaudì
        """
        try:
            # Verifica la corrispondenza del POD
            if attestation_data.get('pod') != self.pod_code:
                raise ValidationError(
                    _("Il POD nell'attestato non corrisponde a quello dell'impianto")
                )

            # Aggiorna i dati con quelli dell'attestato
            gaudi_fields = [
                'gaudi_request_code', 'censimp_code', 'sapr_code', 'validation_date',
                'gaudi_voltage', 'expected_yearly_production', 'expected_operation_date',
                'gaudi_version', 'section_type', 'section_id', 'group_id', 
                'generator_group_id', 'remote_disconnect', 'active_power', 
                'net_power', 'gross_power', 'grid_feed_type', 'has_storage'
            ]
            
            for field in gaudi_fields:
                if field in attestation_data:
                    setattr(self, field, attestation_data[field])

            # Verifica la corrispondenza della potenza
            gaudi_power = float(attestation_data.get('nominal_power', 0))
            if abs(gaudi_power - self.nominal_power) > 0.01:  # 1% di tolleranza
                logger.warning(
                    f"Potenza in Gaudì ({gaudi_power} kW) diversa da quella "
                    f"dell'impianto ({self.nominal_power} kW)"
                )

            self.gaudi_verified = True
            self.save()
            
            logger.info(f"Dati Gaudì verificati per impianto {self.pod_code}")
            return True

        except Exception as e:
            logger.error(f"Errore nella verifica dei dati Gaudì: {str(e)}")
            return False
    
    def validate_gaudi_data(self):
        """Validazioni specifiche per i dati Gaudì"""
        validation_errors = {}

        if not self.gaudi_request_code:
            validation_errors['gaudi_request_code'] = _("Il codice richiesta è obbligatorio per attestati verificati")
        
        if not self.censimp_code:
            validation_errors['censimp_code'] = _("Il codice CENSIMP è obbligatorio per attestati verificati")
            
        if not self.validation_date:
            validation_errors['validation_date'] = _("La data di validazione è obbligatoria per attestati verificati")
        elif self.validation_date > timezone.now():
            validation_errors['validation_date'] = _("La data di validazione non può essere futura")

        if self.expected_yearly_production is not None and self.expected_yearly_production <= 0:
            validation_errors['expected_yearly_production'] = _("La produzione attesa deve essere positiva")

        if self.gaudi_voltage is not None:
            if self.gaudi_voltage <= 0:
                validation_errors['gaudi_voltage'] = _("La tensione deve essere positiva")
            elif self.gaudi_voltage > 500000:  # 500kV come limite massimo ragionevole
                validation_errors['gaudi_voltage'] = _("La tensione inserita supera il valore massimo consentito")

        if validation_errors:
            raise ValidationError(validation_errors)

    
    @classmethod
    def get_total_system_power(cls, user=None, time_window_minutes=5):
        """
        Calcola la potenza totale di tutti gli impianti (o di un utente specifico).
        
        Args:
            user (User, optional): Se specificato, calcola solo per gli impianti dell'utente
            time_window_minutes (int): Finestra temporale in minuti per le misurazioni valide
            
        Returns:
            float: Potenza totale del sistema in kW, arrotondata a 2 decimali
        """
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        # Costruisci la query base
        query = DeviceMeasurement.objects.filter(
            device__is_active=True,
            timestamp__gte=time_threshold,
            quality='GOOD'
        )
        
        # Filtra per utente se specificato
        if user and not user.is_staff:
            query = query.filter(device__plant__owner=user)
            
        # Calcola la potenza totale
        total_power = query.values(
            'device'
        ).annotate(
            latest_power=Max('power')
        ).aggregate(
            total=Sum('latest_power')
        )['total'] or 0
        
        return round(total_power / 1000.0, 2)
        
    def get_total_power(self, time_window_minutes=5):
        """
        Calcola la potenza totale attuale dell'impianto considerando solo le misurazioni recenti
        dei dispositivi attivi.
        """
        # Import locale per evitare l'importazione circolare
        from energy.models import DeviceMeasurement
        from django.db.models import Sum, Max
        
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        total_power = DeviceMeasurement.objects.filter(
            device__plant=self,
            device__is_active=True,
            timestamp__gte=time_threshold,
            quality='GOOD'
        ).values(
            'device'
        ).annotate(
            latest_power=Max('power')
        ).aggregate(
            total=Sum('latest_power')
        )['total'] or 0
        
        return round(total_power / 1000.0, 2)

    @classmethod
    def get_total_system_power(cls, user=None, time_window_minutes=5):
        """
        Calcola la potenza totale di tutti gli impianti.
        """
        # Import locale per evitare l'importazione circolare
        from energy.models import DeviceMeasurement
        from django.db.models import Sum, Max
        
        time_threshold = timezone.now() - timedelta(minutes=time_window_minutes)
        
        query = DeviceMeasurement.objects.filter(
            device__is_active=True,
            timestamp__gte=time_threshold,
            quality='GOOD'
        )
        
        if user and not user.is_staff:
            query = query.filter(device__plant__owner=user)
        
        total_power = query.values(
            'device'
        ).annotate(
            latest_power=Max('power')
        ).aggregate(
            total=Sum('latest_power')
        )['total'] or 0
        
        return round(total_power / 1000.0, 2)

def test_mqtt_connection(self):
    """Test the MQTT connection for this plant"""
    try:
        # Specifichiamo esplicitamente la versione dell'API di callback
        client = mqtt.Client(
            client_id=self.mqtt_client_id,
            protocol=mqtt.MQTTv5,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        
        # Configura le credenziali se necessario
        if self.mqtt_username or (hasattr(settings, 'MQTT_USERNAME') and settings.MQTT_USERNAME):
            username = self.mqtt_username or settings.MQTT_USERNAME
            password = self.mqtt_password or settings.MQTT_PASSWORD
            client.username_pw_set(username, password)

        # Variabile per tracciare lo stato della connessione
        connection_status = {'connected': False}

        # Imposta il callback di connessione
        def on_connect(client, userdata, flags, reason_code, properties):
            connection_status['connected'] = (reason_code == 0)

        client.on_connect = on_connect

        # Tenta la connessione
        try:
            # Usa prima il broker specifico dell'impianto, se presente
            broker = self.mqtt_broker or settings.MQTT_BROKER
            port = self.mqtt_port or settings.MQTT_PORT
            
            client.connect(
                host=broker,
                port=port,
                keepalive=60
            )
            client.loop_start()
            time.sleep(1)  # Breve attesa per permettere la connessione
            client.loop_stop()
            
            # Aggiorna lo stato della connessione nel modello
            self.mqtt_connected = connection_status['connected']
            self.save(update_fields=['mqtt_connected'])
            
            return self.mqtt_connected
            
        except Exception as e:
            self.mqtt_connected = False
            self.save(update_fields=['mqtt_connected'])
            return False
        finally:
            try:
                client.disconnect()
            except:
                pass

    except Exception as e:
        self.mqtt_connected = False
        self.save(update_fields=['mqtt_connected'])
        return False

class PlantMeasurement(models.Model):
    """Misurazioni MQTT dell'impianto"""
    plant = models.ForeignKey(
        Plant,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    timestamp = models.DateTimeField(db_index=True)
    value = models.FloatField()
    variable_type = models.CharField(max_length=50)
    quality = models.CharField(max_length=50, default='GOOD')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['plant', '-timestamp']),
            models.Index(fields=['variable_type', '-timestamp']),
        ]

class PlantDocument(models.Model):
    DOCUMENT_TYPES = [
        ('TECH', 'Documentazione Tecnica'),
        ('LEGAL', 'Documentazione Legale'),
        ('CERT', 'Certificazioni'),
        ('OTHER', 'Altro'),
    ]

    plant = models.ForeignKey(Plant, related_name='documents', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    document = models.FileField(upload_to='plant_documents/')
    document_type = models.CharField(max_length=5, choices=DOCUMENT_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ]

    status = models.CharField(max_length=20)
    severity = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Aggiungi questi campi
    plant = models.ForeignKey(
        'Plant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    status = models.CharField(max_length=20)
    severity = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    cer_configuration = models.ForeignKey(
        'CERConfiguration',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['plant', 'status']),
            models.Index(fields=['cer_configuration', 'status'])
        ]