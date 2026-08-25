from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random

class EmailOTP(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="email_otps")
    otp_code = models.CharField(max_length=6, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTP for {self.user} ({self.otp_code})"

    @classmethod
    def generate_otp(cls, user, minutes=5):
        """สร้าง OTP 6 หลัก และตั้งหมดอายุภายใน X นาที (ดีฟอลต์ 5)"""
        code = f"{random.randint(0, 999999):06d}"
        expires = timezone.now() + timedelta(minutes=minutes)
        cls.objects.filter(user=user, expires_at__lt=timezone.now()).delete()
        return cls.objects.create(user=user, otp_code=code, expires_at=expires)

    def is_valid(self, code: str) -> bool:
        """ตรวจว่าโค้ดตรงและยังไม่หมดอายุ"""
        return self.otp_code == code and timezone.now() <= self.expires_at
