from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class":"border rounded px-3 py-2 w-full"})
    )

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
