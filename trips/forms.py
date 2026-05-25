from django import forms
from django.utils import timezone

from .ecuador_locations import CIUDADES_LIST
from .models import Trip
from .osrm_client import get_route_info


class TripForm(forms.ModelForm):
    origin = forms.CharField(
        label='Origen',
        max_length=255,
        widget=forms.TextInput(attrs={
            'list': 'origin-list',
            'placeholder': 'Escribe una ciudad, terminal o zona...',
            'autocomplete': 'off',
        })
    )
    destination = forms.CharField(
        label='Destino',
        max_length=255,
        widget=forms.TextInput(attrs={
            'list': 'dest-list',
            'placeholder': 'Escribe una ciudad, terminal o zona...',
            'autocomplete': 'off',
        })
    )

    class Meta:
        model = Trip
        fields = ['vehicle', 'origin', 'destination', 'departure_datetime', 'price_per_seat']
        labels = {
            'vehicle': 'Vehículo',
            'departure_datetime': 'Fecha y hora de salida',
            'price_per_seat': 'Precio por asiento ($)',
        }
        widgets = {
            'departure_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.instance_pk = kwargs.get('instance') and kwargs['instance'].pk
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['vehicle'].queryset = self.user.vehicles.all()

    def clean_departure_datetime(self):
        departure = self.cleaned_data['departure_datetime']
        if departure <= timezone.now():
            raise forms.ValidationError("La fecha de salida debe ser futura.")
        return departure

    def clean_price_per_seat(self):
        price = self.cleaned_data['price_per_seat']
        if price <= 0:
            raise forms.ValidationError("El precio debe ser mayor a $0.")
        return price

    def clean(self):
        cleaned_data = super().clean()
        origin = cleaned_data.get('origin')
        destination = cleaned_data.get('destination')
        departure = cleaned_data.get('departure_datetime')
        vehicle = cleaned_data.get('vehicle')

        if origin and destination and origin.strip().lower() == destination.strip().lower():
            self.add_error('destination', "El destino no puede ser igual al origen.")

        if origin and destination and departure and vehicle:
            distance, duration = get_route_info(origin, destination)
            if distance is None or duration is None:
                self.add_error(
                    'origin',
                    "No se pudo calcular la ruta. Verifica que el nombre de la ciudad sea correcto."
                )
            else:
                self.cleaned_data['_distance_km'] = distance
                self.cleaned_data['_duration_minutes'] = duration

                from datetime import timedelta
                end = departure + timedelta(minutes=duration)
                qs = Trip.objects.filter(
                    vehicle=vehicle,
                    status='active',
                    departure_datetime__lt=end,
                    departure_datetime__gte=departure - timedelta(minutes=duration),
                )
                if self.instance_pk:
                    qs = qs.exclude(pk=self.instance_pk)

                overlapping = [
                    t for t in qs
                    if t.departure_datetime < end and t.end_datetime > departure
                ]
                if overlapping:
                    self.add_error(
                        'departure_datetime',
                        "Este vehículo ya tiene un viaje programado que se superpone con este horario."
                    )

        return cleaned_data


class SearchForm(forms.Form):
    origin = forms.CharField(
        label='Origen',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'list': 'origin-list',
            'placeholder': 'Escribe una ciudad...',
            'autocomplete': 'off',
        })
    )
    destination = forms.CharField(
        label='Destino',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'list': 'dest-list',
            'placeholder': 'Escribe una ciudad...',
            'autocomplete': 'off',
        })
    )
    ordering = forms.ChoiceField(
        label='Ordenar por',
        choices=[
            ('-departure_datetime', 'Fecha (más reciente)'),
            ('departure_datetime', 'Fecha (más próximo)'),
            ('price_per_seat', 'Precio (menor a mayor)'),
            ('-price_per_seat', 'Precio (mayor a menor)'),
            ('distance_km', 'Distancia (menor a mayor)'),
        ],
        required=False,
        initial='-departure_datetime',
    )
