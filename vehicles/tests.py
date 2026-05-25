from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Vehicle

User = get_user_model()


class VehicleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='conductor1',
            email='c1@test.com',
            password='testpass123',
            role='conductor',
        )

    def test_vehicle_creation(self):
        vehicle = Vehicle.objects.create(
            owner=self.user,
            brand='Toyota',
            model='Corolla',
            capacity=4,
        )
        self.assertEqual(vehicle.brand, 'Toyota')
        self.assertEqual(vehicle.capacity, 4)
        self.assertEqual(str(vehicle), 'Toyota Corolla (conductor1)')

    def test_capacity_validation(self):
        from django.core.exceptions import ValidationError
        vehicle = Vehicle(owner=self.user, brand='X', model='Y', capacity=0)
        with self.assertRaises(ValidationError):
            vehicle.full_clean()

    def test_available_seats_via_trip(self):
        from trips.models import Trip

        vehicle = Vehicle.objects.create(
            owner=self.user,
            brand='Honda',
            model='Civic',
            capacity=3,
        )
        from django.utils import timezone
        trip = Trip.objects.create(
            driver=self.user,
            vehicle=vehicle,
            origin='A',
            destination='B',
            departure_datetime=timezone.now() + timezone.timedelta(days=1),
            price_per_seat=10,
        )
        self.assertEqual(trip.available_seats, 3)


class VehicleViewTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='conductor2', email='c2@test.com',
            password='testpass123', role='conductor',
        )
        self.pasajero = User.objects.create_user(
            username='pasajero1', email='p1@test.com',
            password='testpass123', role='pasajero',
        )

    def test_conductor_can_access_vehicles(self):
        self.client.login(username='conductor2', password='testpass123')
        response = self.client.get(reverse('vehicles:list'))
        self.assertEqual(response.status_code, 200)

    def test_pasajero_cannot_access_vehicles(self):
        self.client.login(username='pasajero1', password='testpass123')
        response = self.client.get(reverse('vehicles:list'))
        self.assertEqual(response.status_code, 403)

    def test_conductor_can_create_vehicle(self):
        self.client.login(username='conductor2', password='testpass123')
        response = self.client.post(reverse('vehicles:create'), {
            'brand': 'Ford', 'model': 'Focus', 'capacity': 4,
        })
        self.assertRedirects(response, reverse('vehicles:list'))
        self.assertEqual(Vehicle.objects.count(), 1)
        self.assertEqual(Vehicle.objects.first().owner, self.conductor)
