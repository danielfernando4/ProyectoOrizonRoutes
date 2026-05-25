from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import VehicleForm
from .models import Vehicle


class ConductorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'conductor'


class VehicleListView(LoginRequiredMixin, ConductorRequiredMixin, ListView):
    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'

    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)


class VehicleCreateView(LoginRequiredMixin, ConductorRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Vehículo registrado exitosamente.')
        return super().form_valid(form)


class VehicleUpdateView(LoginRequiredMixin, ConductorRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:list')

    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Vehículo actualizado exitosamente.')
        return super().form_valid(form)


class VehicleDeleteView(LoginRequiredMixin, ConductorRequiredMixin, DeleteView):
    model = Vehicle
    template_name = 'vehicles/vehicle_confirm_delete.html'
    success_url = reverse_lazy('vehicles:list')

    def get_queryset(self):
        return Vehicle.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        vehicle = self.get_object()
        if vehicle.trips.filter(status='active', reservations__payment_status='paid').exists():
            messages.error(self.request, 'No se puede eliminar: el vehículo tiene viajes activos con reservas.')
            return redirect('vehicles:list')
        messages.success(self.request, 'Vehículo eliminado exitosamente.')
        return super().form_valid(form)
