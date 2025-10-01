from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.room_create, name="room_create"),
    path("bulk-create/", views.room_bulk_create, name="room_bulk_create"),
    path("<int:pk>/edit/", views.room_edit, name="room_edit"),
    path("<int:pk>/delete/", views.room_delete, name="room_delete"),
    path("<int:pk>/partial/", views.room_detail_partial, name="room_detail_partial"),
    path("<int:pk>/set-status/", views.set_room_status, name="set_room_status"),
    path("<int:pk>/toggle-book/", views.room_toggle_book, name="room_toggle_book"),
    path("<int:pk>/toggle-book/", views.room_toggle_book, name="room_toggle_book"),
]