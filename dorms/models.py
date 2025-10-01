from django.db import models

class Dorm(models.Model):
    name = models.CharField(max_length=120, unique=True)
    address = models.TextField(blank=True)
    max_rooms = models.PositiveIntegerField(default=20)
    image = models.ImageField(upload_to="dorms/", blank=True, null=True)

    def __str__(self):
        return self.name
