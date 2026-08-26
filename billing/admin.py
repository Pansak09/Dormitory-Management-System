from django.contrib import admin

from .models import Bill, BillItem


class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 0


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("room", "billing_month", "total_display", "status", "due_date")
    list_filter = ("status", "room__dorm")
    inlines = [BillItemInline]

    @admin.display(description="ยอดรวม")
    def total_display(self, obj):
        return obj.total_amount
