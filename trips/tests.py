from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Trip, Reservation
from vehicles.models import Vehicle

User = get_user_model()


class TripModelTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='cond1', email='c@t.com', password='p', role='conductor')
        self.vehicle = Vehicle.objects.create(
            owner=self.conductor, brand='A', model='B', capacity=4)
        self.future = timezone.now() + timezone.timedelta(days=2)

    def test_trip_available_seats(self):
        trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='X', destination='Y', departure_datetime=self.future,
            price_per_seat=5,
        )
        self.assertEqual(trip.available_seats, 4)

    def test_trip_available_seats_with_paid(self):
        trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='X', destination='Y', departure_datetime=self.future,
            price_per_seat=5,
        )
        pasajero = User.objects.create_user(
            username='p', email='p@t.com', password='p', role='pasajero')
        Reservation.objects.create(
            passenger=pasajero, trip=trip, payment_status='paid')
        self.assertEqual(trip.available_seats, 3)

    def test_cannot_reserve_own_trip(self):
        trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='X', destination='Y', departure_datetime=self.future,
            price_per_seat=5,
        )
        self.client.login(username='cond1', password='p')
        response = self.client.post(reverse('trips:reserve', kwargs={'pk': trip.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reservation.objects.count(), 0)


class TripViewTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='cond2', email='c2@t.com', password='p', role='conductor')
        self.vehicle = Vehicle.objects.create(
            owner=self.conductor, brand='X', model='Y', capacity=3)
        self.client.login(username='cond2', password='p')
        self.future = timezone.now() + timezone.timedelta(days=1)

    def test_create_trip(self):
        response = self.client.post(reverse('trips:create'), {
            'vehicle': self.vehicle.pk,
            'origin': 'Quito',
            'destination': 'Guayaquil',
            'departure_datetime': (self.future).strftime('%Y-%m-%dT%H:%M'),
            'price_per_seat': 10,
        })
        self.assertRedirects(response, reverse('trips:list'))
        self.assertEqual(Trip.objects.count(), 1)

    def test_create_trip_past_date(self):
        past = timezone.now() - timezone.timedelta(days=1)
        response = self.client.post(reverse('trips:create'), {
            'vehicle': self.vehicle.pk,
            'origin': 'X', 'destination': 'Y',
            'departure_datetime': past.strftime('%Y-%m-%dT%H:%M'),
            'price_per_seat': 10,
        })
        self.assertEqual(Trip.objects.count(), 0)

    def test_search_view(self):
        User.objects.create_user(
            username='p2', email='p2@t.com', password='p', role='pasajero')
        Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='Quito', destination='Guayaquil',
            departure_datetime=self.future, price_per_seat=10, status='active',
        )
        self.client.login(username='p2', password='p')
        response = self.client.get(reverse('trips:search'), {'origin': 'Quito'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quito')

    def test_search_hides_past_trips(self):
        User.objects.create_user(
            username='p3', email='p3@t.com', password='p', role='pasajero')
        past = timezone.now() - timezone.timedelta(days=1)
        Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='OldTrip', destination='Nowhere',
            departure_datetime=past, price_per_seat=5, status='active',
        )
        self.client.login(username='p3', password='p')
        response = self.client.get(reverse('trips:search'), {'origin': 'OldTrip'})
        self.assertContains(response, 'No se encontraron viajes')


class ReservationTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='c', email='c@t.com', password='p', role='conductor')
        self.pasajero = User.objects.create_user(
            username='p', email='p@t.com', password='p', role='pasajero')
        self.vehicle = Vehicle.objects.create(
            owner=self.conductor, brand='A', model='B', capacity=2)
        self.future = timezone.now() + timezone.timedelta(days=1)
        self.trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='A', destination='B',
            departure_datetime=self.future, price_per_seat=10, status='active',
        )

    def test_reservation_model(self):
        reservation = Reservation.objects.create(
            passenger=self.pasajero, trip=self.trip, payment_status='pending')
        self.assertEqual(reservation.payment_status, 'pending')
        self.assertIsNotNone(reservation.created_at)
