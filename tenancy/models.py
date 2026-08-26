from django.conf import settings
from django.db import models

from rooms.models import Room


class TenantRequest(models.Model):
    REQUEST = "REQUEST"
    INVITATION = "INVITATION"
    TYPE_CHOICES = [(REQUEST, "คำขอจากผู้ใช้"), (INVITATION, "คำเชิญจากแอดมิน")]

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STATUS_CHOICES = [(PENDING, "รอดำเนินการ"), (APPROVED, "อนุมัติแล้ว"), (REJECTED, "ปฏิเสธแล้ว")]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="tenant_requests")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tenant_requests")
    request_type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    note = models.TextField(blank=True, help_text="รายละเอียดเพิ่มเติม")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_request_type_display()} ห้อง {self.room.room_number}: {self.user}"
