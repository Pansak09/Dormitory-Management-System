from django.contrib import admin
from .models import Dorm

@admin.register(Dorm)
class DormAdmin(admin.ModelAdmin):
    list_display = ("name","max_rooms")
