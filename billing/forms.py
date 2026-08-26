from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Bill, BillItem


INPUT_CLASS = "mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-indigo-500 focus:ring-indigo-500"


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = [
            "room", "billing_month", "due_date", "room_rent",
            "water_start_unit", "water_current_unit", "water_rate",
            "electricity_start_unit", "electricity_current_unit", "electricity_rate",
            "internet_fee",
        ]
        labels = {
            "room": "ห้อง", "billing_month": "เดือนที่ออกบิล", "due_date": "วันครบกำหนด",
            "room_rent": "ค่าห้อง", "water_start_unit": "หน่วยน้ำเริ่มต้น", "water_current_unit": "หน่วยน้ำปัจจุบัน", "water_rate": "ค่าน้ำ/หน่วย",
            "electricity_start_unit": "หน่วยไฟเริ่มต้น", "electricity_current_unit": "หน่วยไฟปัจจุบัน", "electricity_rate": "ค่าไฟ/หน่วย", "internet_fee": "ค่าอินเทอร์เน็ต",
        }
        widgets = {
            "billing_month": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "room_rent": forms.NumberInput(attrs={"step": "0.01"}),
            "water_start_unit": forms.NumberInput(attrs={"step": "0.01"}), "water_current_unit": forms.NumberInput(attrs={"step": "0.01"}), "water_rate": forms.NumberInput(attrs={"step": "0.01"}),
            "electricity_start_unit": forms.NumberInput(attrs={"step": "0.01"}), "electricity_current_unit": forms.NumberInput(attrs={"step": "0.01"}), "electricity_rate": forms.NumberInput(attrs={"step": "0.01"}),
            "internet_fee": forms.NumberInput(attrs={"step": "0.01"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS
        if not self.is_bound and not self.instance.pk:
            self.fields["billing_month"].initial = timezone.localdate().replace(day=1)

    def clean(self):
        cleaned = super().clean()
        billing_month = cleaned.get("billing_month")
        if billing_month:
            cleaned["billing_month"] = billing_month.replace(day=1)
        room = cleaned.get("room")
        if room and not room.tenant_user_id:
            self.add_error("room", "กรุณากำหนดบัญชีผู้เช่าในข้อมูลห้องก่อนสร้างบิล")
        for start, current, label in [
            ("water_start_unit", "water_current_unit", "น้ำ"),
            ("electricity_start_unit", "electricity_current_unit", "ไฟ"),
        ]:
            if cleaned.get(start) is not None and cleaned.get(current) is not None and cleaned[current] < cleaned[start]:
                self.add_error(current, f"หน่วย{label}ปัจจุบันต้องไม่น้อยกว่าหน่วยเริ่มต้น")
        return cleaned


class BillItemForm(forms.ModelForm):
    class Meta:
        model = BillItem
        fields = ["name", "amount"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT_CLASS, "placeholder": "เช่น ค่าที่จอดรถ"}),
            "amount": forms.NumberInput(attrs={"class": INPUT_CLASS, "step": "0.01", "placeholder": "0.00"}),
        }


BillItemFormSet = inlineformset_factory(Bill, BillItem, form=BillItemForm, extra=2, can_delete=True)


class PaymentSlipForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ["payment_slip"]
        labels = {"payment_slip": "รูปสลิปโอนเงิน"}
        widgets = {"payment_slip": forms.ClearableFileInput(attrs={"accept": "image/*", "class": INPUT_CLASS})}
