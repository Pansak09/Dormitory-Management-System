from django import forms
from .models import Room
    
class DatePickerInput(forms.TextInput):
    input_type = "text" 
    
class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            "dorm", "room_number", "floor", "price_per_month",
            "status", "tenant_name", "tenant_address", "tenant_phone",
            "booking_date", "move_in_date",
        ]
        labels = {
            "room_number": "เลขห้อง",
            "floor": "ชั้น",
            "price_per_month": "ราคา/เดือน (บาท)",
            "status": "สถานะ",
            "tenant_name": "ชื่อผู้เช่า",
            "tenant_phone": "เบอร์โทร",
            "tenant_address": "ที่อยู่",
            "booking_date": "วันที่จอง",
            "move_in_date": "วันเข้าอยู่",
        }
        help_texts = {
            "booking_date": "รูปแบบ YYYY-MM-DD",
            "move_in_date": "รูปแบบ YYYY-MM-DD",
        }
        widgets = {
            "dorm": forms.HiddenInput(),
            "room_number": forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full", "placeholder":"เช่น 001"}),
            "floor": forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full", "min":1}),
            "price_per_month": forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full", "step":"0.01"}),
            "status": forms.Select(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "tenant_name": forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "tenant_phone": forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "tenant_address": forms.Textarea(attrs={"class":"border rounded px-3 py-2 w-full", "rows":3}),
            "booking_date": forms.DateInput(attrs={"type":"date","class":"border rounded px-3 py-2 w-full"}),
            "move_in_date": forms.DateInput(attrs={"type":"date","class":"border rounded px-3 py-2 w-full"}),
        }

    def clean(self):
        data = super().clean()
        if data.get("status") == Room.OCCUPIED and not data.get("tenant_name"):
            self.add_error("tenant_name", "กรุณากรอกชื่อผู้เช่าเมื่อทำการจอง")
        return data


class RoomBulkCreateForm(forms.Form):
    dorm = forms.IntegerField(widget=forms.HiddenInput())
    start_number = forms.IntegerField(min_value=1,
        widget=forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    count = forms.IntegerField(min_value=1, max_value=200,
        widget=forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    digits = forms.IntegerField(min_value=1, max_value=6, initial=3,
        help_text="เช่น 3 หลัก จะได้ 001, 002",
        widget=forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    floor = forms.IntegerField(initial=1,
        widget=forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    price_per_month = forms.DecimalField(initial=3000, max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full", "step":"0.01"}))
    status = forms.ChoiceField(choices=Room.STATUS_CHOICES, initial=Room.VACANT,
        widget=forms.Select(attrs={"class":"border rounded px-3 py-2 w-full"}))
