from django.contrib import admin

from .models import Reservation, Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'departure_datetime', 'price_per_seat', 'status', 'driver')
    list_filter = ('status',)
    search_fields = ('origin', 'destination', 'driver__username')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('trip', 'passenger', 'payment_status', 'created_at')
    list_filter = ('payment_status',)
    search_fields = ('trip__origin', 'trip__destination', 'passenger__username', 'paypal_order_id')
