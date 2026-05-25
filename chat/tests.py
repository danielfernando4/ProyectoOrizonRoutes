from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from trips.models import Trip
from vehicles.models import Vehicle

from .models import ChatRoom, Message

User = get_user_model()


class ChatModelTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='c', email='c@t.com', password='p', role='conductor')
        self.pasajero = User.objects.create_user(
            username='p', email='p@t.com', password='p', role='pasajero')
        self.vehicle = Vehicle.objects.create(
            owner=self.conductor, brand='A', model='B', capacity=4)
        self.trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='A', destination='B',
            departure_datetime=timezone.now() + timezone.timedelta(days=1),
            price_per_seat=10,
        )

    def test_chat_room_creation(self):
        room = ChatRoom.objects.create(
            trip=self.trip, passenger=self.pasajero, driver=self.conductor)
        self.assertIsNotNone(room.pk)
        self.assertEqual(room.trip, self.trip)

    def test_unique_chat_per_trip_passenger(self):
        ChatRoom.objects.create(
            trip=self.trip, passenger=self.pasajero, driver=self.conductor)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ChatRoom.objects.create(
                trip=self.trip, passenger=self.pasajero, driver=self.conductor)

    def test_message_creation(self):
        room = ChatRoom.objects.create(
            trip=self.trip, passenger=self.pasajero, driver=self.conductor)
        msg = Message.objects.create(
            room=room, sender=self.pasajero, content='Hola')
        self.assertEqual(msg.content, 'Hola')
        self.assertEqual(room.messages.count(), 1)


class ChatViewTests(TestCase):
    def setUp(self):
        self.conductor = User.objects.create_user(
            username='c', email='c@t.com', password='p', role='conductor')
        self.pasajero = User.objects.create_user(
            username='p', email='p@t.com', password='p', role='pasajero')
        self.vehicle = Vehicle.objects.create(
            owner=self.conductor, brand='A', model='B', capacity=4)
        self.trip = Trip.objects.create(
            driver=self.conductor, vehicle=self.vehicle,
            origin='A', destination='B',
            departure_datetime=timezone.now() + timezone.timedelta(days=1),
            price_per_seat=10,
        )

    def test_start_chat_creates_room(self):
        self.client.login(username='p', password='p')
        response = self.client.get(reverse('chat:start', kwargs={'pk': self.trip.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChatRoom.objects.count(), 1)

    def test_chat_room_view(self):
        room = ChatRoom.objects.create(
            trip=self.trip, passenger=self.pasajero, driver=self.conductor)
        self.client.login(username='p', password='p')
        response = self.client.get(reverse('chat:room', kwargs={'pk': room.pk}))
        self.assertEqual(response.status_code, 200)

    def test_chat_room_access_denied(self):
        room = ChatRoom.objects.create(
            trip=self.trip, passenger=self.pasajero, driver=self.conductor)
        extra = User.objects.create_user(
            username='extra', email='e@t.com', password='p', role='pasajero')
        self.client.login(username='extra', password='p')
        response = self.client.get(reverse('chat:room', kwargs={'pk': room.pk}))
        self.assertEqual(response.status_code, 404)
