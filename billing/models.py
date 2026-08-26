from decimal import Decimal

from django.db import models
from django.utils import timezone

from rooms.models import Room


class Bill(models.Model):
    OVERDUE = "OVERDUE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    PAID = "PAID"
    STATUS_CHOICES = [
        (OVERDUE, "ค้างชำระ"),
        (PENDING_VERIFICATION, "รอตรวจสอบการโอนเงิน"),
        (PAID, "ชำระเงินแล้ว"),
    ]

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bills")
    billing_month = models.DateField(help_text="เลือกวันใดก็ได้ในเดือนที่ต้องการออกบิล")
    due_date = models.DateField()
    room_rent = models.DecimalField(max_digits=10, decimal_places=2)
    water_start_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_current_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_start_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_current_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electricity_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    internet_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=OVERDUE)
    payment_slip = models.ImageField(upload_to="payment_slips/%Y/%m/", blank=True, null=True)
    slip_uploaded_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["room", "billing_month"], name="uq_bill_room_month")
        ]
        ordering = ["-billing_month", "room__room_number"]

    @property
    def water_units_used(self):
        return max(Decimal("0"), self.water_current_unit - self.water_start_unit)

    @property
    def water_fee(self):
        return self.water_units_used * self.water_rate

    @property
    def electricity_units_used(self):
        return max(Decimal("0"), self.electricity_current_unit - self.electricity_start_unit)

    @property
    def electricity_fee(self):
        return self.electricity_units_used * self.electricity_rate

    @property
    def extra_total(self):
        return sum((item.amount for item in self.items.all()), Decimal("0"))

    @property
    def total_amount(self):
        return self.room_rent + self.water_fee + self.electricity_fee + self.internet_fee + self.extra_total

    @property
    def month_label(self):
        return self.billing_month.strftime("%m/%Y")

    def __str__(self):
        return f"บิลห้อง {self.room.room_number} เดือน {self.month_label}"


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name
