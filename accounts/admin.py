from django.contrib import admin

from .models import EmailOTP, TenantProfile

admin.site.register(EmailOTP)
admin.site.register(TenantProfile)
