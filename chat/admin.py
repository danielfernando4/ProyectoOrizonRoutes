from django.contrib import admin

from .models import ChatRoom, Message


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('trip', 'passenger', 'driver', 'created_at')
    search_fields = ('trip__origin', 'trip__destination', 'passenger__username', 'driver__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'content', 'sent_at')
    search_fields = ('sender__username', 'content')
