from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from allauth.socialaccount.forms import SignupForm as SocialSignupForm

from .models import TenantProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class":"border rounded px-3 py-2 w-full"})
    )
    full_name = forms.CharField(label="ชื่อ-นามสกุล", max_length=120,
        widget=forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    phone = forms.CharField(label="เบอร์โทร", max_length=30,
        widget=forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}))
    address = forms.CharField(label="ที่อยู่", widget=forms.Textarea(attrs={"class":"border rounded px-3 py-2 w-full", "rows":3}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "password1": forms.PasswordInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
            "password2": forms.PasswordInput(attrs={"class":"border rounded px-3 py-2 w-full"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("อีเมลนี้มีผู้ใช้งานแล้ว")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            TenantProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": self.cleaned_data["full_name"],
                    "phone": self.cleaned_data["phone"],
                    "address": self.cleaned_data["address"],
                },
            )
        return user


class GoogleSocialSignupForm(SocialSignupForm):
    """ฟอร์มครั้งแรกหลังกลับมาจาก Google เพื่อเก็บข้อมูลผู้เช่าให้ครบ."""
    full_name = forms.CharField(label="ชื่อ-นามสกุล", max_length=120)
    phone = forms.CharField(label="เบอร์โทร", max_length=30)
    address = forms.CharField(label="ที่อยู่", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = self.sociallogin.account.extra_data.get("name", "")
        self.fields["full_name"].initial = name
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} w-full rounded-lg border border-gray-300 px-3 py-2".strip()

    def save(self, request):
        user = super().save(request)
        TenantProfile.objects.update_or_create(
            user=user,
            defaults={
                "full_name": self.cleaned_data["full_name"],
                "phone": self.cleaned_data["phone"],
                "address": self.cleaned_data["address"],
            },
        )
        return user
