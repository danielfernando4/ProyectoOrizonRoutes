from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.ChatListView.as_view(), name="list"),
    path("<int:pk>/", views.ChatRoomView.as_view(), name="room"),
    path("start/<int:pk>/", views.StartChatView.as_view(), name="start"),
]
