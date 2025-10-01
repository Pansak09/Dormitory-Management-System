# accounts/urls.py
from django.urls import path
from .views import MyLoginView, signup, my_logout

urlpatterns = [
    path("login/",  MyLoginView.as_view(), name="login"),
    path("logout/", my_logout,name="logout"),  # <-- ใช้ฟังก์ชันใหม่
    path("signup/", signup,name="signup"),
]

