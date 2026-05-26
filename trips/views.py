from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView,
    DetailView, FormView, View,
)

import logging

logger = logging.getLogger(__name__)

from .forms import TripForm, SearchForm
from .models import Trip, Reservation
from .paypal_client import get_paypal_client
from .ecuador_locations import CIUDADES_LIST

ITEMS_PER_PAGE = 9


class ConductorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'conductor'


class PasajeroRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'pasajero'


class TripListView(LoginRequiredMixin, ConductorRequiredMixin, ListView):
    model = Trip
    template_name = 'trips/trip_list.html'
    context_object_name = 'trips'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        qs = Trip.objects.filter(driver=self.request.user)
        tab = self.request.GET.get('tab', 'active')
        if tab == 'past':
            qs = qs.filter(
                departure_datetime__lte=timezone.now()
            ).exclude(status='cancelled')
        elif tab == 'cancelled':
            qs = qs.filter(status='cancelled')
        else:
            qs = qs.filter(status='active')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'active')
        return context


class TripCreateView(LoginRequiredMixin, ConductorRequiredMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/trip_form.html'
    success_url = reverse_lazy('trips:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if not request.user.vehicles.exists():
            messages.warning(request, 'Debe registrar un vehículo antes de publicar un viaje.')
            return redirect('vehicles:create')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.driver = self.request.user
        form.instance.distance_km = form.cleaned_data.get('_distance_km', 0)
        form.instance.duration_minutes = form.cleaned_data.get('_duration_minutes', 0)
        messages.success(self.request, 'Viaje publicado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['CIUDADES_LIST'] = CIUDADES_LIST
        return context


class TripUpdateView(LoginRequiredMixin, ConductorRequiredMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name = 'trips/trip_form.html'
    success_url = reverse_lazy('trips:list')

    def get_queryset(self):
        qs = Trip.objects.filter(driver=self.request.user)
        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        trip = self.get_object()
        if trip.reserved_seats > 0:
            messages.error(request, 'No se puede editar: el viaje ya tiene reservas confirmadas.')
            return redirect('trips:list')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.distance_km = form.cleaned_data.get('_distance_km', 0)
        form.instance.duration_minutes = form.cleaned_data.get('_duration_minutes', 0)
        messages.success(self.request, 'Viaje actualizado exitosamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['CIUDADES_LIST'] = CIUDADES_LIST
        return context


class TripDeleteView(LoginRequiredMixin, ConductorRequiredMixin, DeleteView):
    model = Trip
    template_name = 'trips/trip_confirm_delete.html'
    success_url = reverse_lazy('trips:list')

    def get_queryset(self):
        return Trip.objects.filter(driver=self.request.user)

    def form_valid(self, form):
        trip = self.get_object()
        if trip.reserved_seats > 0:
            messages.error(self.request, 'No se puede eliminar: el viaje tiene reservas confirmadas.')
            return redirect('trips:list')
        messages.success(self.request, 'Viaje eliminado.')
        return super().form_valid(form)


class SearchView(LoginRequiredMixin, PasajeroRequiredMixin, FormView):
    template_name = 'trips/search.html'
    form_class = SearchForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET' and self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()

        origin = ''
        destination = ''
        ordering = '-departure_datetime'
        has_filters = False

        if form.is_valid():
            origin = form.cleaned_data.get('origin', '')
            destination = form.cleaned_data.get('destination', '')
            ordering = form.cleaned_data.get('ordering', '-departure_datetime')
            if origin or destination:
                has_filters = True

        page = request.GET.get('page', 1)

        trips_qs = Trip.objects.select_related(
            'driver', 'vehicle'
        ).prefetch_related('reservations').filter(
            status='active',
            departure_datetime__gt=timezone.now(),
        )

        if origin:
            trips_qs = trips_qs.filter(origin__icontains=origin)
        if destination:
            trips_qs = trips_qs.filter(destination__icontains=destination)

        trips = [t for t in trips_qs if t.available_seats > 0]

        sort_reverse = ordering.startswith('-')
        sort_field = ordering.lstrip('-')
        trips.sort(
            key=lambda t: self._sort_key(t, sort_field),
            reverse=sort_reverse,
        )

        paginator = Paginator(trips, ITEMS_PER_PAGE)
        try:
            page_obj = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        context = self.get_context_data(
            form=form,
            trips=page_obj,
            page_obj=page_obj,
            origin_filter=origin,
            destination_filter=destination,
            current_ordering=ordering,
            total_results=len(trips),
            has_filters=has_filters,
            CIUDADES_LIST=CIUDADES_LIST,
        )
        return self.render_to_response(context)

    @staticmethod
    def _sort_key(trip, field):
        if field == 'price_per_seat':
            return float(trip.price_per_seat) if trip.price_per_seat else 0
        elif field == 'distance_km':
            return float(trip.distance_km) if trip.distance_km else 0
        return trip.departure_datetime


class TripDetailView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = 'trips/trip_detail.html'
    context_object_name = 'trip'


class CancelTripView(LoginRequiredMixin, ConductorRequiredMixin, DetailView):
    model = Trip
    template_name = 'trips/trip_cancel.html'
    context_object_name = 'trip'

    def get_queryset(self):
        return Trip.objects.filter(driver=self.request.user, status='active')

    def post(self, request, *args, **kwargs):
        trip = self.get_object()

        paypal = get_paypal_client()

        trip.status = 'cancelled'
        trip.save()

        refunded_count = 0
        for reservation in trip.reservations.filter(payment_status='paid'):
            try:
                paypal.refund_capture(reservation.paypal_capture_id)
                reservation.payment_status = 'refunded'
                reservation.save()
                refunded_count += 1
            except Exception:
                messages.error(request, f'Error al reembolsar reserva #{reservation.id}.')

        if refunded_count > 0:
            messages.success(request, f'Viaje cancelado. {refunded_count} reembolso(s) procesado(s).')
        else:
            messages.success(request, 'Viaje cancelado.')

        return redirect('trips:list')


class CreateReservationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk, status='active')

        if request.user == trip.driver:
            messages.error(request, 'No puedes reservar tu propio viaje.')
            return redirect('trips:detail', pk=trip.pk)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
        if quantity < 1:
            quantity = 1

        with transaction.atomic():
            trip = Trip.objects.select_for_update().get(pk=trip.pk)
            if trip.available_seats < quantity:
                messages.error(
                    request,
                    f'No hay suficientes asientos. Solicitaste {quantity} pero solo hay {trip.available_seats} disponible(s).'
                )
                return redirect('trips:detail', pk=trip.pk)

            reservation = Reservation.objects.create(
                passenger=request.user,
                trip=trip,
                quantity=quantity,
            )

            """
            paypal = get_paypal_client()
            return_url = request.build_absolute_uri(reverse('trips:capture'))
            cancel_url = request.build_absolute_uri(
                reverse('trips:detail', kwargs={'pk': trip.pk})
            )

            total = trip.price_per_seat * quantity

            try:
                order_id, approval_link = paypal.create_order(
                    value=total,
                    return_url=return_url,
                    cancel_url=cancel_url,
                )
                reservation.paypal_order_id = order_id
                reservation.save()
                return redirect(approval_link)
            except Exception as e:
                logger.exception("PayPal create_order failed")
                reservation.delete()
                messages.error(request, f'Error al procesar el pago. Intenta nuevamente. ({e})')
                return redirect('trips:detail', pk=trip.pk)
            """

            # MODO DESARROLLO (sin PayPal)

            reservation.payment_status = 'paid'
            reservation.save()

            messages.success(request, 'Reserva realizada correctamente.')
            return redirect('trips:reservation_success', pk=reservation.pk)


class CaptureOrderView(LoginRequiredMixin, View):
    def get(self, request):
        order_id = request.GET.get('token')
        if not order_id:
            messages.error(request, 'Token de orden no encontrado.')
            return redirect('home')

        reservation = get_object_or_404(Reservation, paypal_order_id=order_id, passenger=request.user)

        if reservation.payment_status == 'paid':
            return redirect('trips:reservation_success', pk=reservation.pk)

        paypal = get_paypal_client()

        try:
            capture_id, _ = paypal.capture_order(order_id)
            reservation.paypal_capture_id = capture_id
            reservation.payment_status = 'paid'
            reservation.save()
            return redirect('trips:reservation_success', pk=reservation.pk)
        except Exception:
            messages.error(request, 'Error al confirmar el pago. Contacta al soporte.')
            return redirect('trips:detail', pk=reservation.trip.pk)


class ReservationSuccessView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = 'trips/reservation_success.html'
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.filter(passenger=self.request.user)


class PassengerReservationListView(LoginRequiredMixin, PasajeroRequiredMixin, ListView):
    template_name = 'trips/passenger_reservations.html'
    context_object_name = 'reservations'
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        return Reservation.objects.filter(
            passenger=self.request.user,
            payment_status='paid',
        ).select_related('trip', 'trip__driver').order_by('-created_at')
