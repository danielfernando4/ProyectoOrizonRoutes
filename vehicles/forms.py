from django import forms
from .models import Vehicle


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['brand', 'model', 'capacity']
        labels = {
            'brand': 'Marca',
            'model': 'Modelo',
            'capacity': 'Capacidad de asientos',
        }

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']
        if capacity < 1:
            raise forms.ValidationError("La capacidad debe ser al menos 1.")
        return capacity
