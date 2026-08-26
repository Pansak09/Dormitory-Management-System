from django import forms
from django.contrib.auth import get_user_model

from rooms.models import Room
from accounts.models import TenantProfile
from .models import TenantRequest


INPUT_CLASS = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-indigo-500 focus:ring-indigo-500"


class TenantRequestForm(forms.ModelForm):
    class Meta:
        model = TenantRequest
        fields = ["room", "full_name", "phone", "address", "note"]
        labels = {"room": "ห้องที่ต้องการเข้าพัก", "full_name": "ชื่อ-นามสกุล", "phone": "เบอร์โทร", "address": "ที่อยู่", "note": "ข้อความถึงแอดมิน (ถ้ามี)"}
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 3, "placeholder": "เช่น ชื่อผู้เช่าตรงกับสัญญา..."}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.filter(tenant_user__isnull=True).select_related("dorm").order_by("dorm__name", "room_number")
        self.fields["room"].label_from_instance = lambda room: f"{room.dorm.name} - ห้อง {room.room_number}"
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS
        if user and not self.is_bound:
            profile = TenantProfile.objects.filter(user=user).first()
            self.fields["full_name"].initial = profile.full_name if profile else (user.get_full_name() or user.username)
            self.fields["phone"].initial = profile.phone if profile else ""
            self.fields["address"].initial = profile.address if profile else ""

    def clean(self):
        cleaned = super().clean()
        for field in ("full_name", "phone", "address"):
            if not cleaned.get(field):
                self.add_error(field, "กรุณากรอกข้อมูลนี้")
        return cleaned


class TenantInviteForm(forms.ModelForm):
    class Meta:
        model = TenantRequest
        fields = ["room", "user", "note"]
        labels = {"room": "ห้อง", "user": "เชิญผู้ใช้", "note": "ข้อความถึงผู้เช่า (ถ้ามี)"}
        widgets = {"note": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["room"].queryset = Room.objects.filter(tenant_user__isnull=True).select_related("dorm").order_by("dorm__name", "room_number")
        self.fields["room"].label_from_instance = lambda room: f"{room.dorm.name} - ห้อง {room.room_number}"
        self.fields["user"].queryset = get_user_model().objects.filter(is_staff=False).order_by("username")
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS
