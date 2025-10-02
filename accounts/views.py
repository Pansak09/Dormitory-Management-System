import random
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.views import LoginView, PasswordResetView
from django.urls import reverse_lazy

from .forms import SignUpForm
from .models import EmailOTP

User = get_user_model()

# -------------------- LOGIN & SIGNUP (มีอยู่แล้วก็ใช้ต่อได้) --------------------

class MyLoginView(LoginView):
    template_name = "accounts/login.html"
    success_url = reverse_lazy("dorm_list")

def my_logout(request):
    logout(request)
    return redirect("login")

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]
            user = authenticate(username=user.username, password=raw_password)
            if user:
                login(request, user)
                return redirect("dorm_list")
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})

# -------------------- OTP EMAIL RESET PASSWORD --------------------

def _send_otp_email(to_email: str, first_name: str, code: str):
    """ส่งอีเมล OTP ไปยังผู้ใช้"""
    subject = "รหัส OTP สำหรับรีเซ็ตรหัสผ่าน (หมดอายุภายใน 5 นาที)"
    body = (
        f"สวัสดี {first_name or ''}\n\n"
        f"รหัส OTP ของคุณคือ: {code}\n"
        f"**รหัสจะหมดอายุภายใน 5 นาที**\n\n"
        f"หากคุณไม่ได้ร้องขอ กรุณาเพิกเฉยอีเมลฉบับนี้"
    )
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)
    send_mail(subject, body, from_email, [to_email], fail_silently=False)

@csrf_protect
@never_cache
def request_otp_view(request):
    """ขอ OTP ผ่านอีเมล"""
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "กรุณากรอกอีเมล")
            return redirect("request_otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "ไม่พบอีเมลนี้ในระบบ")
            return redirect("request_otp")

        otp_obj = EmailOTP.generate_otp(user=user, minutes=5)
        _send_otp_email(user.email, getattr(user, "first_name", ""), otp_obj.otp_code)

        request.session["otp_user_id"] = user.id
        request.session["otp_requested_at"] = timezone.now().isoformat()
        messages.success(request, "เราได้ส่งรหัส OTP ไปที่อีเมลของคุณแล้ว")
        return redirect("verify_otp")

    return render(request, "otp/request_otp.html")

@csrf_protect
@never_cache
def verify_otp_view(request):
    """ตรวจสอบ OTP"""
    user_id = request.session.get("otp_user_id")
    if not user_id:
        messages.error(request, "เซสชันหมดอายุ กรุณาขอรหัสใหม่")
        return redirect("request_otp")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "ไม่พบผู้ใช้")
        return redirect("request_otp")

    if request.method == "POST":
        code = (request.POST.get("otp") or "").strip()
        if not code:
            messages.error(request, "กรุณากรอกรหัส OTP")
            return redirect("verify_otp")

        try:
            otp_obj = EmailOTP.objects.filter(user=user).latest("created_at")
        except EmailOTP.DoesNotExist:
            messages.error(request, "ไม่พบรหัส OTP กรุณาขอรหัสใหม่")
            return redirect("request_otp")

        if otp_obj.is_valid(code):
            request.session["otp_verified"] = True
            messages.success(request, "ยืนยัน OTP สำเร็จ โปรดตั้งรหัสผ่านใหม่")
            return redirect("reset_password_custom")
        else:
            messages.error(request, "รหัส OTP ไม่ถูกต้องหรือหมดอายุแล้ว")
            return redirect("verify_otp")

    return render(request, "otp/verify_otp.html")

@csrf_protect
@never_cache
def reset_password_custom(request):
    """รีเซ็ตรหัสผ่านใหม่หลังจากยืนยัน OTP"""
    if not request.session.get("otp_verified"):
        messages.error(request, "ยังไม่ได้ยืนยัน OTP")
        return redirect("request_otp")

    user_id = request.session.get("otp_user_id")
    if not user_id:
        messages.error(request, "เซสชันหมดอายุ กรุณาขอรหัสใหม่")
        return redirect("request_otp")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "ไม่พบผู้ใช้")
        return redirect("request_otp")

    if request.method == "POST":
        new_password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""

        if len(new_password) < 8:
            messages.error(request, "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
            return redirect("reset_password_custom")

        if new_password != confirm_password:
            messages.error(request, "รหัสผ่านไม่ตรงกัน")
            return redirect("reset_password_custom")

        user.set_password(new_password)
        user.save()

        # เคลียร์ session ที่เกี่ยวกับ OTP
        for key in ["otp_user_id", "otp_verified", "otp_requested_at"]:
            request.session.pop(key, None)

        messages.success(request, "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว สามารถเข้าสู่ระบบได้")
        return redirect("login")

    return render(request, "otp/reset_password_custom.html")

# (ถ้าใช้ Password Reset แบบลิงก์อีเมลด้วย ให้คง CustomPasswordResetView นี้ไว้)
class CustomPasswordResetView(PasswordResetView):
    """บังคับ domain/protocol ในอีเมล reset password"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["domain"] = getattr(settings, "DEFAULT_DOMAIN", "127.0.0.1:8000")
        context["protocol"] = getattr(settings, "DEFAULT_PROTOCOL", "http")
        return context
