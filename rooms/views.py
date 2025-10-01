# rooms/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django import forms
from django.template.loader import render_to_string
import json

from dorms.models import Dorm
from dorms.utils import is_staff_user
from .models import Room
from .forms import RoomForm


# ---------- อ่านอย่างเดียว (public) ----------

def room_detail_partial(request, pk):
    """แผงรายละเอียดห้อง (โหลดด้วย HTMX) – ใครๆ ดูได้"""
    r = get_object_or_404(Room, pk=pk)
    return render(request, "rooms/_detail_panel.html", {"r": r})


# ---------- จัดการ (เฉพาะ staff/superuser) ----------

@user_passes_test(is_staff_user)
def room_create(request):
    dorm_id = request.GET.get("dorm_id") or request.POST.get("dorm")
    dorm = get_object_or_404(Dorm, pk=dorm_id) if dorm_id else None

    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            if dorm:
                room.dorm = dorm
            room.save()
            return redirect("dorm_detail", pk=room.dorm_id)
    else:
        form = RoomForm(initial={"dorm": dorm.id if dorm else None})

    return render(request, "rooms/create.html", {"form": form, "dorm": dorm})


@user_passes_test(is_staff_user)
def room_edit(request, pk):
    """
    แก้ไขห้องผ่านแผงด้านขวา (HTMX)
    - POST สำเร็จ: ส่ง panel ใหม่ + การ์ดห้อง OOB + trigger room-changed
    - GET: ส่งฟอร์มแก้ไข (_detail_panel_edit.html)
    """
    room = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            room = form.save()

            # 1) partial panel ด้านขวา
            panel_html = render_to_string("rooms/_detail_panel.html", {"r": room}, request=request)

            # 2) partial "การ์ดห้อง" เพื่อแทนที่ในการ์ดกริด (OOB)
            card_html = render_to_string("rooms/_card.html", {"r": room, "user": request.user}, request=request)
            oob_wrapper = f'\n<div id="room-card-{room.id}" hx-swap-oob="outerHTML">{card_html}</div>'

            resp = HttpResponse(panel_html + oob_wrapper)

            # 3) Trigger ให้ส่วนสรุป/แดชบอร์ดรีโหลด (ถ้ามีตั้ง hx-trigger ไว้)
            resp["HX-Trigger"] = json.dumps({"room-changed": {"dorm": room.dorm_id, "room": room.id}})
            return resp
        else:
            # ฟอร์มไม่ผ่าน ก็ส่งฟอร์มกลับไปแก้
            html = render_to_string("rooms/_detail_panel_edit.html", {"r": room, "form": form}, request=request)
            return HttpResponse(html, status=400)

    # GET
    form = RoomForm(instance=room)
    html = render_to_string("rooms/_detail_panel_edit.html", {"r": room, "form": form}, request=request)
    return HttpResponse(html)


@user_passes_test(is_staff_user)
def room_toggle_book(request, pk):
    """
    สลับสถานะ ว่าง(vacant) <-> จองแล้ว(booked) จากปุ่มบนการ์ด
    - POST เท่านั้น
    - ส่ง panel ใหม่ + การ์ดห้อง OOB + trigger room-changed
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    r = get_object_or_404(Room, pk=pk)

    VACANT = getattr(Room, "VACANT", "vacant")
    BOOKED = getattr(Room, "BOOKED", "booked")

    r.status = BOOKED if r.status == VACANT else VACANT
    r.save()

    panel_html = render_to_string("rooms/_detail_panel.html", {"r": r}, request=request)
    card_html = render_to_string("rooms/_card.html", {"r": r, "user": request.user}, request=request)
    oob = f'\n<div id="room-card-{r.id}" hx-swap-oob="outerHTML">{card_html}</div>'

    resp = HttpResponse(panel_html + oob)
    resp["HX-Trigger"] = json.dumps({"room-changed": {"dorm": r.dorm_id, "room": r.id}})
    return resp


@user_passes_test(is_staff_user)
def set_room_status(request, pk):
    """
    (ออปชัน) ตั้งค่าสถานะตรง ๆ ผ่าน query string ?status=vacant|booked|occupied
    ใช้สำหรับกรณีต้องการลิงก์เร็ว ๆ; ปกติแนะนำใช้ room_toggle_book แทน
    """
    r = get_object_or_404(Room, pk=pk)
    status = request.GET.get("status")
    if status in dict(Room.STATUS_CHOICES):
        r.status = status
        r.save()
    return render(request, "rooms/_detail_panel.html", {"r": r})


@user_passes_test(is_staff_user)
def room_delete(request, pk):
    r = get_object_or_404(Room, pk=pk)
    dorm_id = r.dorm_id
    if request.method == "POST":
        r.delete()
        # ถ้ามาจาก HTMX ให้รีไดเร็กต์ไปหน้ารายละเอียดหอ
        if request.headers.get("HX-Request"):
            resp = HttpResponse("", status=204)
            resp["HX-Redirect"] = reverse("dorm_detail", kwargs={"pk": dorm_id})
            return resp
        return redirect("dorm_detail", pk=dorm_id)
    return render(request, "rooms/delete.html", {"r": r})


# ---------- เพิ่มหลายห้อง ----------

class RoomBulkForm(forms.Form):
    dorm = forms.IntegerField(widget=forms.HiddenInput)

    start_number = forms.IntegerField(label="เริ่มจากเลขห้อง", initial=1, min_value=0)
    count = forms.IntegerField(label="จำนวนห้องที่จะสร้าง", initial=10, min_value=1, max_value=300)
    digits = forms.IntegerField(label="จำนวนหลัก (padding)", initial=3, min_value=1, max_value=6)

    floor = forms.IntegerField(label="ชั้น", initial=1)
    price_per_month = forms.DecimalField(label="ราคา/เดือน", max_digits=10, decimal_places=2, initial=3000)
    status = forms.ChoiceField(label="สถานะเริ่มต้น", choices=Room.STATUS_CHOICES, initial=getattr(Room, "VACANT", "vacant"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "dorm":
                continue
            css = "border rounded px-3 py-2 w-full"
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " " + css).strip()


@user_passes_test(is_staff_user)
def room_bulk_create(request):
    dorm_id = request.GET.get("dorm_id") or request.POST.get("dorm")
    dorm = get_object_or_404(Dorm, pk=dorm_id) if dorm_id else None

    if request.method == "POST":
        form = RoomBulkForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd["start_number"]
            stop = start + cd["count"]
            created = 0

            for i in range(start, stop):
                number = str(i).zfill(cd["digits"])
                obj, _created = Room.objects.get_or_create(
                    dorm=dorm,
                    room_number=number,
                    defaults={
                        "floor": cd["floor"],
                        "price_per_month": cd["price_per_month"],
                        "status": cd["status"],
                    },
                )
                if _created:
                    created += 1
            return redirect("dorm_detail", pk=dorm.id)
    else:
        initial = {"dorm": dorm.id if dorm else None}
        form = RoomBulkForm(initial=initial)

    return render(request, "rooms/bulk_create.html", {"form": form, "dorm": dorm})
