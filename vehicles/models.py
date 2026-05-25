from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Vehicle(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
    )
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ['brand', 'model']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.owner})"

    def clean(self):
        if self.capacity < 1:
            raise ValidationError({'capacity': "La capacidad debe ser al menos 1."})
