from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    trip = models.ForeignKey(
        'trips.Trip',
        on_delete=models.CASCADE,
        related_name='chat_rooms',
    )
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_passenger',
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_driver',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sala de chat"
        verbose_name_plural = "Salas de chat"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['trip', 'passenger'],
                name='unique_chat_per_trip_passenger',
            ),
        ]

    def __str__(self):
        return f"Chat: {self.trip} - {self.passenger}"


class Message(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_messages',
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['room', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}"
