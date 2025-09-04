# Esempi di Management Commands per CerCollettiva
# Questi sono esempi di comandi Django personalizzati

# energy/management/commands/example_energy_calculation.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from energy.models import DeviceMeasurement
from energy.services.energy_calculator_cache import EnergyCalculatorCache
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Esempio di comando per calcoli energetici'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=str,
            help='ID del dispositivo per il calcolo',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Numero di giorni per il calcolo (default: 7)',
        )

    def handle(self, *args, **options):
        device_id = options['device_id']
        days = options['days']
        
        if not device_id:
            self.stdout.write(
                self.style.ERROR('Device ID richiesto')
            )
            return
        
        self.stdout.write(f'Calcolo energia per dispositivo {device_id} per {days} giorni...')
        
        try:
            calculator = EnergyCalculatorCache()
            end_date = timezone.now()
            start_date = end_date - timezone.timedelta(days=days)
            
            # Calcola energia giornaliera
            daily_energy = calculator.calculate_daily_energy(
                device_id=device_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_energy = sum(day['energy'] for day in daily_energy)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Energia totale: {total_energy:.2f} kWh'
                )
            )
            
            for day_data in daily_energy:
                self.stdout.write(
                    f"  {day_data['date']}: {day_data['energy']:.2f} kWh"
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore nel calcolo: {str(e)}')
            )
            logger.error(f'Errore comando energy calculation: {str(e)}')


# core/management/commands/example_cer_setup.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import CERConfiguration, Plant
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Esempio di setup CER di test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cer-name',
            type=str,
            default='CER di Test',
            help='Nome della CER di test',
        )

    def handle(self, *args, **options):
        cer_name = options['cer_name']
        
        self.stdout.write(f'Creazione CER di test: {cer_name}')
        
        try:
            # Crea utente admin se non esiste
            admin_user, created = User.objects.get_or_create(
                username='admin_test',
                defaults={
                    'email': 'admin@test.com',
                    'first_name': 'Admin',
                    'last_name': 'Test',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                self.stdout.write('Utente admin creato')
            else:
                self.stdout.write('Utente admin già esistente')
            
            # Crea CER di test
            cer, created = CERConfiguration.objects.get_or_create(
                name=cer_name,
                defaults={
                    'code': 'CER_TEST_001',
                    'vat_number': '12345678901',
                    'address': 'Via Test 1',
                    'city': 'Milano',
                    'province': 'MI',
                    'zip_code': '20100',
                    'email': 'info@test.com',
                    'phone': '+390212345678',
                    'admin': admin_user,
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write('CER di test creata')
            else:
                self.stdout.write('CER di test già esistente')
            
            # Crea impianto di test
            plant, created = Plant.objects.get_or_create(
                name='Impianto Test',
                defaults={
                    'code': 'PLANT_TEST_001',
                    'type': 'PHOTOVOLTAIC',
                    'power_kw': Decimal('100.00'),
                    'address': 'Via Impianto 1',
                    'city': 'Milano',
                    'province': 'MI',
                    'zip_code': '20100',
                    'latitude': Decimal('45.4642'),
                    'longitude': Decimal('9.1900'),
                    'owner': admin_user,
                    'cer': cer,
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write('Impianto di test creato')
            else:
                self.stdout.write('Impianto di test già esistente')
            
            self.stdout.write(
                self.style.SUCCESS('Setup CER di test completato!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore nel setup: {str(e)}')
            )


# documents/management/commands/example_document_processing.py
from django.core.management.base import BaseCommand
from documents.models import Document
from documents.processors.gaudi import GAUDIProcessor
import os

class Command(BaseCommand):
    help = 'Esempio di elaborazione documenti GAUDI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file-path',
            type=str,
            help='Percorso del file GAUDI da elaborare',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        if not file_path or not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR('File path valido richiesto')
            )
            return
        
        self.stdout.write(f'Elaborazione documento: {file_path}')
        
        try:
            # Crea documento
            document = Document.objects.create(
                name=os.path.basename(file_path),
                file_path=file_path,
                document_type='GAUDI',
            )
            
            # Elabora con GAUDI processor
            processor = GAUDIProcessor(file_path)
            result = processor.process()
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS('Documento elaborato con successo!')
                )
                self.stdout.write(f'POD trovato: {result.get("pod", "N/A")}')
                self.stdout.write(f'Dati estratti: {len(result.get("data", {}))} campi')
            else:
                self.stdout.write(
                    self.style.ERROR(f'Errore nell\'elaborazione: {result.get("error")}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Errore: {str(e)}')
            )
