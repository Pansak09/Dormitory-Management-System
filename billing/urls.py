from django.urls import path

from . import views


urlpatterns = [
    path("", views.bill_list, name="bill_list"),
    path("create/", views.bill_create, name="bill_create"),
    path("<int:pk>/", views.bill_detail, name="bill_detail"),
    path("<int:pk>/upload-slip/", views.upload_slip, name="bill_upload_slip"),
    path("<int:pk>/verify/", views.verify_payment, name="bill_verify_payment"),
]
