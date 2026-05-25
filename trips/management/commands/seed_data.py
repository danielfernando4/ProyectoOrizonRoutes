"""
Management command to seed test data for the Viajes Compartidos application.
Creates 5 passengers, 5 conductors (with vehicles and trips with OSRM-calculated routes).

Usage:
    python manage.py seed_data
    python manage.py seed_data --reset   (delete existing non-admin users first)
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from trips.models import Trip
from trips.osrm_client import get_route_info
from vehicles.models import Vehicle

User = get_user_model()

CONDUCTORS = [
    {"username": "carlos.m", "email": "carlos@email.com", "first_name": "Carlos", "last_name": "Mendoza"},
    {"username": "maria.l", "email": "maria@email.com", "first_name": "María", "last_name": "López"},
    {"username": "jose.r", "email": "jose@email.com", "first_name": "José", "last_name": "Ramírez"},
    {"username": "ana.v", "email": "ana@email.com", "first_name": "Ana", "last_name": "Vásquez"},
    {"username": "pedro.g", "email": "pedro@email.com", "first_name": "Pedro", "last_name": "Gómez"},
]

PASSENGERS = [
    {"username": "lucia.f", "email": "lucia@email.com", "first_name": "Lucía", "last_name": "Fernández"},
    {"username": "diego.p", "email": "diego@email.com", "first_name": "Diego", "last_name": "Paredes"},
    {"username": "sofia.c", "email": "sofia@email.com", "first_name": "Sofía", "last_name": "Castro"},
    {"username": "andres.t", "email": "andres@email.com", "first_name": "Andrés", "last_name": "Torres"},
    {"username": "elena.r", "email": "elena@email.com", "first_name": "Elena", "last_name": "Ríos"},
]

VEHICLES = [
    {"brand": "Toyota", "model": "Corolla", "capacity": 4},
    {"brand": "Hyundai", "model": "Tucson", "capacity": 5},
    {"brand": "Chevrolet", "model": "Aveo", "capacity": 4},
    {"brand": "Kia", "model": "Sportage", "capacity": 5},
    {"brand": "Nissan", "model": "Sentra", "capacity": 4},
]

# Routes in Ecuador — cities as origins/destinations
ROUTES = [
    {"origin": "Quito", "destination": "Guayaquil", "price": 15.00},
    {"origin": "Quito", "destination": "Cuenca", "price": 12.00},
    {"origin": "Guayaquil", "destination": "Cuenca", "price": 10.00},
    {"origin": "Cuenca", "destination": "Loja", "price": 9.00},
    {"origin": "Ambato", "destination": "Baños de Agua Santa", "price": 3.00},
    {"origin": "Quito", "destination": "Otavalo", "price": 4.00},
    {"origin": "Guayaquil", "destination": "Salinas", "price": 7.00},
    {"origin": "Quito", "destination": "Mitad del Mundo", "price": 2.00},
    {"origin": "Quito", "destination": "Mindo", "price": 5.00},
    {"origin": "Esmeraldas", "destination": "Atacames", "price": 3.00},
    {"origin": "Manta", "destination": "Puerto López", "price": 5.00},
    {"origin": "Quito", "destination": "Carcelén (Quito)", "price": 2.00},
    {"origin": "Guayaquil", "destination": "Montañita", "price": 9.00},
    {"origin": "Quito", "destination": "Papallacta", "price": 4.00},
    {"origin": "Riobamba", "destination": "Baños de Agua Santa", "price": 3.00},
    {"origin": "Quito", "destination": "Sangolquí", "price": 2.00},
    {"origin": "Santa Elena", "destination": "Montañita", "price": 4.00},
    {"origin": "Ibarra", "destination": "Tulcán", "price": 6.00},
]

PASSWORD = "viaje123"


class Command(BaseCommand):
    help = "Seed the database with test users, vehicles, and trips for development."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing non-admin users, vehicles, and trips before seeding.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Reseteando datos...")
            Trip.objects.all().delete()
            Vehicle.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Datos anteriores eliminados."))

        self._create_passengers()
        self._create_conductors()
        self.stdout.write(self.style.SUCCESS("Datos de prueba creados exitosamente."))

    def _create_passengers(self):
        self.stdout.write("Creando pasajeros...")
        for data in PASSENGERS:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": "pasajero",
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(f"  + Pasajero: {user.get_full_name()} ({user.username})")
            else:
                self.stdout.write(f"  = Pasajero ya existe: {user.username}")

    def _create_conductors(self):
        self.stdout.write("Creando conductores, vehículos y viajes...")
        now = timezone.now()

        for i, data in enumerate(CONDUCTORS):
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "role": "conductor",
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()

            vdata = VEHICLES[i]
            vehicle, _ = Vehicle.objects.get_or_create(
                owner=user,
                brand=vdata["brand"],
                model=vdata["model"],
                defaults={"capacity": vdata["capacity"]},
            )

            # Give each conductor 3 trips spread across future days
            trip_count = 0
            for j, route in enumerate(ROUTES):
                if trip_count >= 3:
                    break
                # Only create if it doesn't already exist for this driver
                departure = now + timedelta(days=j + 1, hours=j * 2 + 6)
                if not Trip.objects.filter(
                    driver=user, origin=route["origin"],
                    destination=route["destination"],
                ).exists():
                    self.stdout.write(f"  Calculando rutas para {user.get_full_name()}...")
                    distance, duration = get_route_info(route["origin"], route["destination"])
                    Trip.objects.create(
                        driver=user,
                        vehicle=vehicle,
                        origin=route["origin"],
                        destination=route["destination"],
                        departure_datetime=departure,
                        price_per_seat=route["price"],
                        distance_km=distance or 0,
                        duration_minutes=duration or 0,
                        status="active",
                    )
                    trip_count += 1

            trip_count_real = Trip.objects.filter(driver=user).count()
            icon = "+" if created else "="
            self.stdout.write(
                f"  {icon} Conductor: {user.get_full_name()} | "
                f"Vehículo: {vehicle.brand} {vehicle.model} | "
                f"{trip_count_real} viaje(s)"
            )

        total = Trip.objects.count()
        self.stdout.write(f"  Total viajes creados: {total}")
