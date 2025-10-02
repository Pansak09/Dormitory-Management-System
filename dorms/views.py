from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import Dorm
from rooms.models import Room
from .forms import DormForm
from .utils import is_staff_user  

from django.db.models import Count, Q
from django.shortcuts import render
import json

from django.http import HttpResponse
from django.template.loader import render_to_string


# --- utils ---
def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# --- views ---

@login_required
def dorm_list(request):
    dorms = Dorm.objects.all().order_by("name")
    return render(request, "dorms/list.html", {"dorms": dorms})


# รายละเอียดหอ/กริดห้อง – ใครๆ ดูได้
@login_required
def dorm_detail(request, pk):
    dorm = get_object_or_404(Dorm, pk=pk)
    rooms = Room.objects.filter(dorm=dorm).order_by("room_number")
    return render(request, "dorms/detail.html", {"dorm": dorm, "rooms": rooms})


# สร้างหอ – เฉพาะ staff/superuser
@user_passes_test(is_staff_user)
def dorm_create(request):
    if request.method == "POST":
        form = DormForm(request.POST, request.FILES)
        if form.is_valid():
            dorm = form.save()
            return redirect("dorm_detail", pk=dorm.pk)
    else:
        form = DormForm()
    return render(request, "dorms/create.html", {"form": form})


# แก้ไขหอ – เฉพาะ staff/superuser
@user_passes_test(is_staff_user)
def dorm_edit(request, pk):
    dorm = get_object_or_404(Dorm, pk=pk)
    if request.method == "POST":
        form = DormForm(request.POST, request.FILES, instance=dorm)
        if form.is_valid():
            form.save()
            return redirect("dorm_detail", pk=dorm.pk)
    else:
        form = DormForm(instance=dorm)
    return render(request, "dorms/edit.html", {"form": form, "dorm": dorm})


# ลบหอ – เฉพาะ staff/superuser
@user_passes_test(is_staff_user)
def dorm_delete(request, pk):
    dorm = get_object_or_404(Dorm, pk=pk)
    if request.method == "POST":
        dorm.delete()
        return redirect("dorm_list")
    return render(request, "dorms/delete.html", {"dorm": dorm})


# Dashboard – เฉพาะ staff/superuser
@login_required
@user_passes_test(_is_staff)
def dashboard(request):
    dorm_id = request.GET.get("dorm")
    current_dorm = None

    room_qs = Room.objects.all()
    if dorm_id:
        current_dorm = get_object_or_404(Dorm, pk=dorm_id)
        room_qs = room_qs.filter(dorm_id=dorm_id)

    # ใช้ status ตามโมเดล
    VACANT = getattr(Room, "VACANT", "vacant")
    OCCUPIED = getattr(Room, "OCCUPIED", "occupied")

    total_dorms = Dorm.objects.count()
    total_rooms = room_qs.count()
    count_vacant = room_qs.filter(status=VACANT).count()
    count_occupied = room_qs.filter(status=OCCUPIED).count()

    # จำนวนห้องต่อหอ (Top 10)
    by_dorm_queryset = Room.objects.all()
    if dorm_id:
        by_dorm_queryset = by_dorm_queryset.filter(dorm_id=dorm_id)

    by_dorm = (
        by_dorm_queryset.values("dorm__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )
    by_dorm_labels = [x["dorm__name"] for x in by_dorm]
    by_dorm_counts = [x["total"] for x in by_dorm]

    all_dorms = Dorm.objects.order_by("name").values("id", "name")

    context = {
        "total_dorms": total_dorms,
        "total_rooms": total_rooms,
        "count_vacant": count_vacant,
        "count_occupied": count_occupied,
        "by_dorm_labels": json.dumps(by_dorm_labels, ensure_ascii=False),
        "by_dorm_counts": json.dumps(by_dorm_counts),
        "current_dorm": current_dorm,
        "all_dorms": list(all_dorms),
    }
    return render(request, "dashboard/index.html", context)


# partial สำหรับ refresh counters (htmx)
@login_required
@user_passes_test(_is_staff)
def dashboard_counters_partial(request):
    dorm_id = request.GET.get("dorm")
    current = Dorm.objects.filter(pk=dorm_id).first() if dorm_id else None

    qs = Room.objects.all()
    if current:
        qs = qs.filter(dorm=current)

    VACANT = getattr(Room, "VACANT", "vacant")
    OCCUPIED = getattr(Room, "OCCUPIED", "occupied")

    ctx = {
        "total_dorms": Dorm.objects.count(),
        "total_rooms": qs.count(),
        "count_vacant": qs.filter(status=VACANT).count(),
        "count_occupied": qs.filter(status=OCCUPIED).count(),
    }
    html = render_to_string("dashboard/_counters.html", ctx, request=request)
    return HttpResponse(html)
