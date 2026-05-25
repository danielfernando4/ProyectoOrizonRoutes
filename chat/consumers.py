import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import ChatRoom, Message


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            self.close()
            return

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        try:
            self.chat_room = ChatRoom.objects.get(pk=self.room_id)
        except ChatRoom.DoesNotExist:
            self.close()
            return

        if self.user != self.chat_room.passenger and self.user != self.chat_room.driver:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("message", "").strip()
        if not content:
            return

        message = Message.objects.create(
            room=self.chat_room,
            sender=self.user,
            content=content,
        )

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": content,
                "sender": self.user.username,
                "sender_name": self.user.get_full_name() or self.user.username,
                "sent_at": message.sent_at.strftime("%H:%M"),
            },
        )

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "sender_name": event["sender_name"],
            "sent_at": event["sent_at"],
        }))
