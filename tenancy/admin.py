from django.contrib import admin

from .models import TenantRequest


@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "request_type", "status", "created_at")
    list_filter = ("request_type", "status", "room__dorm")
