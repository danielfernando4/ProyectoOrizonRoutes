from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView

from trips.models import Trip

from .models import ChatRoom


class ChatListView(LoginRequiredMixin, ListView):
    template_name = 'chat/chat_list.html'
    context_object_name = 'chat_rooms'

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            models.Q(passenger=user) | models.Q(driver=user)
        ).select_related('trip', 'passenger', 'driver')


class ChatRoomView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'chat/chat_room.html'
    context_object_name = 'chat_room'

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            models.Q(passenger=user) | models.Q(driver=user)
        )


class StartChatView(LoginRequiredMixin, DetailView):
    model = Trip
    template_name = None

    def get(self, request, *args, **kwargs):
        trip = self.get_object()
        if request.user == trip.driver:
            return redirect('trips:detail', pk=trip.pk)

        room, _ = ChatRoom.objects.get_or_create(
            trip=trip,
            passenger=request.user,
            defaults={'driver': trip.driver},
        )

        return redirect('chat:room', pk=room.pk)
