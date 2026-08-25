from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("logout/", views.my_logout, name="logout"),
    path("signup/", views.signup, name="signup"),

    # ระบบ OTP รีเซ็ตรหัสผ่าน
    path("password/otp/request/", views.request_otp_view, name="request_otp"),
    path("password/otp/verify/", views.verify_otp_view, name="verify_otp"),
    path("password/otp/reset/", views.reset_password_custom, name="reset_password_custom"),
]