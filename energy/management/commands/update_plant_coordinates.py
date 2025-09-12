# energy/management/commands/update_plant_coordinates.py

from django.core.management.base import BaseCommand
from core.main_models import Plant
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time

class Command(BaseCommand):
    help = 'Aggiorna le coordinate geografiche degli impianti'

    def handle(self, *args, **options):
        geolocator = Nominatim(
            user_agent="cercollettiva",
            timeout=10  # Aumenta il timeout a 10 secondi
        )
        
        plants = Plant.objects.filter(latitude__isnull=True).exclude(address='')
        total = plants.count()
        
        self.stdout.write(f"Trovati {total} impianti da aggiornare")
        
        for i, plant in enumerate(plants, 1):
            self.stdout.write(f"Elaborazione impianto {i}/{total}: {plant.name}")
            
            # Costruisci l'indirizzo completo
            full_address = f"{plant.address}, {plant.zip_code} {plant.city} {plant.province}, Italy"
            
            # Tentativi multipli con pause più lunghe
            for attempt in range(5):  # Aumenta il numero di tentativi a 5
                try:
                    location = geolocator.geocode(full_address)
                    
                    if location:
                        plant.latitude = location.latitude
                        plant.longitude = location.longitude
                        plant.save(update_fields=['latitude', 'longitude'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Coordinate aggiornate per {plant.name}: "
                                f"lat={location.latitude}, lon={location.longitude}"
                            )
                        )
                        break
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Nessuna coordinata trovata per: {plant.name}"
                            )
                        )
                        break
                        
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    if attempt == 4:  # Ultimo tentativo
                        self.stdout.write(
                            self.style.ERROR(
                                f"Impossibile ottenere le coordinate per: {plant.name}"
                            )
                        )
                    else:
                        self.stdout.write(f"Tentativo {attempt + 1} fallito, riprovo...")
                        time.sleep(2)  # Pausa di 2 secondi tra i tentativi
            
            # Pausa tra gli impianti per rispettare i limiti di OpenStreetMap
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Aggiornamento coordinate completato'))
