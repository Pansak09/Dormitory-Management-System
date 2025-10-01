from django.urls import path
from . import views

urlpatterns = [
    path("", views.dorm_list, name="dorm_list"),
    path("create/", views.dorm_create, name="dorm_create"),
    path("<int:pk>/", views.dorm_detail, name="dorm_detail"),
    path("<int:pk>/edit/", views.dorm_edit, name="dorm_edit"),
    path("<int:pk>/delete/", views.dorm_delete, name="dorm_delete"), 
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/counters/", views.dashboard_counters_partial, name="dashboard_counters"),

    
]
