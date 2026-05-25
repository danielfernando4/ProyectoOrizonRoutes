import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Sum


def _generate_reservation_code():
    return uuid.uuid4().hex[:8].upper()


class Trip(models.Model):
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('cancelled', 'Cancelado'),
        ('finished', 'Finalizado'),
    ]

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trips_as_driver',
    )
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        on_delete=models.PROTECT,
        related_name='trips',
    )
    origin = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    departure_datetime = models.DateTimeField()
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2)
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=1, default=0,
        help_text="Distancia de la ruta en kilómetros (calculado por OSRM)"
    )
    duration_minutes = models.PositiveIntegerField(
        default=0,
        help_text="Duración estimada del viaje en minutos (calculado por OSRM)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )

    class Meta:
        verbose_name = "Viaje"
        verbose_name_plural = "Viajes"
        ordering = ['-departure_datetime']
        indexes = [
            models.Index(fields=['departure_datetime', 'status']),
            models.Index(fields=['origin', 'destination']),
            models.Index(fields=['price_per_seat']),
        ]

    def __str__(self):
        return f"{self.origin} -> {self.destination} ({self.departure_datetime})"

    @property
    def end_datetime(self):
        if self.duration_minutes:
            return self.departure_datetime + timedelta(minutes=self.duration_minutes)
        return self.departure_datetime

    @property
    def reserved_seats(self):
        total = self.reservations.filter(payment_status='paid').aggregate(
            total=Sum('quantity')
        )['total']
        return total or 0

    @property
    def available_seats(self):
        return self.vehicle.capacity - self.reserved_seats

    @property
    def is_full(self):
        return self.available_seats <= 0

    @property
    def has_departed(self):
        from django.utils import timezone
        return self.departure_datetime <= timezone.now()


class Reservation(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('refunded', 'Reembolsado'),
    ]

    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        related_name='reservations',
    )
    paypal_order_id = models.CharField(max_length=255, blank=True, null=True)
    paypal_capture_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad de asientos reservados en esta transacción"
    )
    reservation_code = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trip', 'payment_status']),
            models.Index(fields=['paypal_order_id']),
        ]

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            self.reservation_code = _generate_reservation_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.passenger} -> {self.trip} ({self.reservation_code})"
