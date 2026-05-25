from django.urls import path

from . import views

app_name = "trips"

urlpatterns = [
    path("", views.TripListView.as_view(), name="list"),
    path("create/", views.TripCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.TripUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.TripDeleteView.as_view(), name="delete"),
    path("<int:pk>/detail/", views.TripDetailView.as_view(), name="detail"),
    path("<int:pk>/cancel/", views.CancelTripView.as_view(), name="cancel"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("<int:pk>/reserve/", views.CreateReservationView.as_view(), name="reserve"),
    path("capture/", views.CaptureOrderView.as_view(), name="capture"),
    path("reservation/<int:pk>/success/", views.ReservationSuccessView.as_view(), name="reservation_success"),
    path("my-reservations/", views.PassengerReservationListView.as_view(), name="passenger_reservations"),
]
