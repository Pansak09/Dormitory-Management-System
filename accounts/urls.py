from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ------------------------
    # Auth: Login / Logout / Signup
    # ------------------------
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("logout/", views.my_logout, name="logout"),
    path("signup/", views.signup, name="signup"),

    # ------------------------
    # OTP Reset Password (Custom)
    # ------------------------
    path("password/otp/request/", views.request_otp_view, name="request_otp"),
    path("password/otp/verify/", views.verify_otp_view, name="verify_otp"),
    path("password/otp/reset/", views.reset_password_custom, name="reset_password_custom"),

    # ------------------------
    # Password Reset (Email Link) ✅ ใช้ CustomPasswordResetView
    # ------------------------
    path(
        "password-reset/",
        views.CustomPasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.txt",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url="/accounts/password-reset/done/",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url="/accounts/reset/done/",
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
