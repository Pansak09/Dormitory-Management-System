from django.urls import path

from . import views


urlpatterns = [
    path("", views.tenancy_manage, name="tenancy_manage"),
    path("request/<int:room_id>/", views.create_request, name="tenancy_request"),
    path("invite/", views.create_invitation, name="tenancy_invite"),
    path("<int:pk>/approve/", views.approve_request, name="tenancy_approve"),
    path("<int:pk>/accept/", views.accept_invitation, name="tenancy_accept"),
    path("<int:pk>/reject/", views.reject_request, name="tenancy_reject"),
]
