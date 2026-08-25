from django.db import models
from dorms.models import Dorm

class Room(models.Model):
    VACANT = "VACANT"
    OCCUPIED = "OCCUPIED"
    STATUS_CHOICES = [(VACANT, "ยังไม่จอง"), (OCCUPIED, "จองแล้ว")]

    dorm = models.ForeignKey(Dorm, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=VACANT)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2, default=3000)
    floor = models.IntegerField(default=1)
    
    tenant_name = models.CharField(max_length=120, blank=True)
    tenant_address = models.TextField(blank=True)
    tenant_phone = models.CharField(max_length=30, blank=True)
    
    booking_date = models.DateField(blank=True, null=True)   
    move_in_date = models.DateField(blank=True, null=True)   

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["dorm", "room_number"], name="uq_room_per_dorm")
        ]

    def __str__(self):
        return f"{self.dorm.name} - {self.room_number}"
