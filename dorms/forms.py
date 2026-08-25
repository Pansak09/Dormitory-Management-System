from django import forms
from .models import Dorm

class DormForm(forms.ModelForm):
    class Meta:
        model = Dorm
        fields = ["name","address","max_rooms","image"]
        widgets = {
            "name": forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "address": forms.Textarea(attrs={"rows":3,"class":"border rounded px-3 py-2 w-full"}),
            "max_rooms": forms.NumberInput(attrs={"class":"border rounded px-3 py-2 w-full","min":1}),
        }
