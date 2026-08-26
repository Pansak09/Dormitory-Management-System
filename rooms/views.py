# rooms/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django import forms
from django.db.models.deletion import ProtectedError
from django.template.loader import render_to_string
import json

from dorms.models import Dorm
from dorms.utils import is_staff_user
from .models import Room
from .forms import RoomForm

def room_detail_partial(request, pk):
    r = get_object_or_404(Room, pk=pk)
    tenant_request = None
    if request.user.is_authenticated and not is_staff_user(request.user):
        from tenancy.models import TenantRequest
        tenant_request = TenantRequest.objects.filter(
            room=r, user=request.user, status=TenantRequest.PENDING
        ).first()
    return render(request, "rooms/_detail_panel.html", {"r": r, "tenant_request": tenant_request})

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
    r = get_object_or_404(Room, pk=pk)

    if request.method == "POST":
        form = RoomForm(request.POST, instance=r)
        if form.is_valid():
            r = form.save()
            if request.headers.get("HX-Request"):
                return render(request, "rooms/_detail_panel.html", {"r": r})
            return redirect("dorm_detail", pk=r.dorm_id)
    else:
        form = RoomForm(instance=r)
        
    if request.headers.get("HX-Request"):
        return render(request, "rooms/_edit_form.html", {"form": form, "r": r})

    return render(request, "rooms/edit.html", {"form": form, "r": r})

@user_passes_test(is_staff_user)
def room_toggle_book(request, pk):
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
        if request.headers.get("HX-Request"):
            resp = HttpResponse("", status=204)
            resp["HX-Redirect"] = reverse("dorm_detail", kwargs={"pk": dorm_id})
            return resp
        return redirect("dorm_detail", pk=dorm_id)
    return render(request, "rooms/delete.html", {"r": r})

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


@user_passes_test(is_staff_user)
def room_bulk_delete(request):
    dorm_id = request.GET.get("dorm_id") or request.POST.get("dorm_id")
    dorm = get_object_or_404(Dorm, pk=dorm_id)

    if request.method == "POST":
        action = request.POST.get("action")
        rooms = Room.objects.filter(dorm=dorm)
        if action == "floor":
            floor = request.POST.get("floor")
            rooms = rooms.filter(floor=floor)
            description = f"ห้องทั้งหมดชั้น {floor}"
        else:
            room_ids = request.POST.getlist("room_ids")
            rooms = rooms.filter(pk__in=room_ids)
            description = "ห้องที่เลือก"

        count = rooms.count()
        if not count:
            messages.error(request, "กรุณาเลือกห้องที่ต้องการลบ")
        else:
            try:
                rooms.delete()
                messages.success(request, f"ลบ{description} {count} ห้องเรียบร้อยแล้ว")
            except ProtectedError:
                messages.error(request, "ไม่สามารถลบห้องที่มีบิลค่าเช่าอยู่ได้ กรุณาเก็บประวัติบิลไว้หรือจัดการบิลก่อน")
        return redirect("dorm_detail", pk=dorm.pk)

    rooms = list(Room.objects.filter(dorm=dorm).order_by("floor", "room_number"))
    floors = {}
    for room in rooms:
        floors.setdefault(room.floor, []).append(room)
    return render(request, "rooms/bulk_delete.html", {"dorm": dorm, "floors": floors})
