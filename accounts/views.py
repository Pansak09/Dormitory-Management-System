from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignUpForm  # ดูไฟล์ forms.py ที่ให้ไว้ก่อนหน้า

class MyLoginView(LoginView):
    template_name = "accounts/login.html"

def my_logout(request):
    logout(request)
    return redirect("login")

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw = form.cleaned_data["password1"]
            user = authenticate(username=user.username, password=raw)
            if user:
                login(request, user)
                return redirect("dorm_list")
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})
