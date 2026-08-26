from django.contrib import messages
from django import forms
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dorms.utils import is_staff_user
from accounts.models import TenantProfile
from .forms import TenantInviteForm, TenantRequestForm
from .models import TenantRequest


def _is_admin(user):
    return user.is_staff or user.is_superuser


def _complete_tenancy(tenant_request):
    """ผูกบัญชีเข้ากับห้องและมอบกลุ่ม Tenant ในครั้งเดียว."""
    room = tenant_request.room
    room.tenant_user = tenant_request.user
    room.status = room.OCCUPIED
    room.tenant_name = tenant_request.full_name or tenant_request.user.get_full_name() or tenant_request.user.username
    room.tenant_phone = tenant_request.phone
    room.tenant_address = tenant_request.address
    room.save(update_fields=["tenant_user", "status", "tenant_name", "tenant_phone", "tenant_address"])
    tenant_group, _ = Group.objects.get_or_create(name="Tenant")
    tenant_request.user.groups.add(tenant_group)
    tenant_request.status = TenantRequest.APPROVED
    tenant_request.completed_at = timezone.now()
    tenant_request.save(update_fields=["status", "completed_at"])
    # ห้องหนึ่งมีผู้เช่าได้เพียงบัญชีเดียว จึงปิดรายการที่รอของห้องเดียวกันทั้งหมด
    TenantRequest.objects.filter(room=room, status=TenantRequest.PENDING).exclude(pk=tenant_request.pk).update(
        status=TenantRequest.REJECTED,
        completed_at=timezone.now(),
    )


@login_required
def tenancy_manage(request):
    if _is_admin(request.user):
        pending = TenantRequest.objects.filter(status=TenantRequest.PENDING).select_related("room", "room__dorm", "user")
        return render(request, "tenancy/manage.html", {"pending": pending, "invite_form": TenantInviteForm()})
    return redirect("dorm_list")


@login_required
def create_request(request, room_id):
    if _is_admin(request.user):
        return redirect("tenancy_manage")
    if request.user.rented_rooms.exists():
        messages.error(request, "บัญชีนี้เป็นผู้เช่าอยู่แล้ว")
        return redirect("dorm_list")
    if request.method == "POST":
        form = TenantRequestForm(request.POST, user=request.user)
    else:
        form = TenantRequestForm(initial={"room": room_id}, user=request.user)
        form.fields["room"].widget = forms.HiddenInput()
    if request.method == "POST" and form.is_valid():
        room = form.cleaned_data["room"]
        if room.pk != room_id:
            messages.error(request, "ห้องที่เลือกไม่ถูกต้อง")
            return redirect("dorm_list")
        if TenantRequest.objects.filter(user=request.user, room=room, status=TenantRequest.PENDING).exists():
            messages.error(request, "คุณส่งคำขอสำหรับห้องนี้แล้ว")
        else:
            item = form.save(commit=False)
            item.user = request.user
            item.request_type = TenantRequest.REQUEST
            item.save()
            TenantProfile.objects.update_or_create(
                user=request.user,
                defaults={
                    "full_name": item.full_name,
                    "phone": item.phone,
                    "address": item.address,
                },
            )
            messages.success(request, "ส่งคำขอแล้ว รอแอดมินอนุมัติ")
        return redirect("dorm_detail", pk=room.dorm_id)
    if request.method == "POST":
        messages.error(request, "กรุณาตรวจสอบข้อมูลคำขอ")
    return render(request, "tenancy/request_form.html", {"form": form, "room_id": room_id})


@user_passes_test(is_staff_user)
def create_invitation(request):
    if request.method != "POST":
        return redirect("tenancy_manage")
    form = TenantInviteForm(request.POST)
    if form.is_valid():
        room = form.cleaned_data["room"]
        user = form.cleaned_data["user"]
        if TenantRequest.objects.filter(room=room, status=TenantRequest.PENDING).exists():
            messages.error(request, "ห้องนี้มีคำขอหรือคำเชิญที่รอดำเนินการอยู่")
        else:
            invitation = form.save(commit=False)
            invitation.request_type = TenantRequest.INVITATION
            invitation.save()
            messages.success(request, f"ส่งคำเชิญให้ {user.username} แล้ว")
    else:
        messages.error(request, "กรุณาตรวจสอบข้อมูลคำเชิญ")
    return redirect("tenancy_manage")


@user_passes_test(is_staff_user)
def approve_request(request, pk):
    item = get_object_or_404(TenantRequest, pk=pk, request_type=TenantRequest.REQUEST, status=TenantRequest.PENDING)
    if request.method == "POST":
        with transaction.atomic():
            item.refresh_from_db()
            if item.room.tenant_user_id:
                messages.error(request, "ห้องนี้มีผู้เช่าแล้ว")
            else:
                _complete_tenancy(item)
                messages.success(request, "อนุมัติผู้เช่าเรียบร้อยแล้ว")
    return redirect("tenancy_manage")


@login_required
def accept_invitation(request, pk):
    item = get_object_or_404(TenantRequest, pk=pk, user=request.user, request_type=TenantRequest.INVITATION, status=TenantRequest.PENDING)
    if request.method == "POST":
        with transaction.atomic():
            item.refresh_from_db()
            if item.room.tenant_user_id:
                messages.error(request, "ห้องนี้มีผู้เช่าแล้ว")
            elif request.user.rented_rooms.exists():
                messages.error(request, "บัญชีนี้เป็นผู้เช่าอยู่แล้ว")
            else:
                _complete_tenancy(item)
                messages.success(request, "ตอบรับคำเชิญแล้ว คุณเป็นผู้เช่าของห้องนี้เรียบร้อย")
    return redirect("tenancy_manage")


@login_required
def reject_request(request, pk):
    item = get_object_or_404(TenantRequest, pk=pk, status=TenantRequest.PENDING)
    allowed = _is_admin(request.user) or (item.user_id == request.user and item.request_type == TenantRequest.INVITATION)
    if request.method == "POST" and allowed:
        item.status = TenantRequest.REJECTED
        item.completed_at = timezone.now()
        item.save(update_fields=["status", "completed_at"])
        messages.success(request, "ปฏิเสธรายการเรียบร้อยแล้ว")
    return redirect("tenancy_manage")
