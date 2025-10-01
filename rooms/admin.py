from django.contrib import admin
from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number","dorm","status","floor","price_per_month")
    list_filter = ("dorm","status","floor")
