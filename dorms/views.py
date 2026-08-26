from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .models import Dorm
from rooms.models import Room
from .forms import DormForm
from .utils import is_staff_user  

from django.db.models import Count, Q
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import render
import json

from django.http import HttpResponse
from django.template.loader import render_to_string

def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required
def dorm_list(request):
    dorms = Dorm.objects.all().order_by("name")
    return render(request, "dorms/list.html", {"dorms": dorms})

@login_required
def dorm_detail(request, pk):
    dorm = get_object_or_404(Dorm, pk=pk)
    rooms = list(Room.objects.filter(dorm=dorm))

    def room_sort_key(r):
        try:
            number_key = int(r.room_number)
        except (TypeError, ValueError):
            number_key = r.room_number  # fallback: sort non-numeric text as-is
        return (r.floor, number_key)

    rooms.sort(key=room_sort_key)
    return render(request, "dorms/detail.html", {"dorm": dorm, "rooms": rooms})

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

@user_passes_test(is_staff_user)
def dorm_delete(request, pk):
    dorm = get_object_or_404(Dorm, pk=pk)
    if request.method == "POST":
        dorm.delete()
        return redirect("dorm_list")
    return render(request, "dorms/delete.html", {"dorm": dorm})

@login_required
@user_passes_test(_is_staff)
def dashboard(request):
    from billing.models import Bill

    dorm_id = request.GET.get("dorm")
    current_dorm = None

    room_qs = Room.objects.all()
    if dorm_id:
        current_dorm = get_object_or_404(Dorm, pk=dorm_id)
        room_qs = room_qs.filter(dorm_id=dorm_id)

    VACANT = getattr(Room, "VACANT", "vacant")
    OCCUPIED = getattr(Room, "OCCUPIED", "occupied")

    total_dorms = Dorm.objects.count()
    total_rooms = room_qs.count()
    count_vacant = room_qs.filter(status=VACANT).count()
    count_occupied = room_qs.filter(status=OCCUPIED).count()

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

    current_month = timezone.localdate().replace(day=1)
    bill_qs = Bill.objects.select_related("room", "room__dorm").prefetch_related("items")
    if dorm_id:
        bill_qs = bill_qs.filter(room__dorm_id=dorm_id)
    monthly_bills = list(bill_qs.filter(billing_month=current_month))
    paid_bills = [bill for bill in monthly_bills if bill.status == Bill.PAID]
    unpaid_bills = [bill for bill in monthly_bills if bill.status == Bill.OVERDUE]
    pending_bills = [bill for bill in monthly_bills if bill.status == Bill.PENDING_VERIFICATION]
    monthly_income = sum((bill.total_amount for bill in paid_bills), Decimal("0"))
    outstanding_amount = sum((bill.total_amount for bill in unpaid_bills), Decimal("0"))
    pending_amount = sum((bill.total_amount for bill in pending_bills), Decimal("0"))
    recent_bills = list(bill_qs.order_by("-billing_month", "due_date")[:6])
    recent_tenants = Room.objects.filter(tenant_user__isnull=False)
    if dorm_id:
        recent_tenants = recent_tenants.filter(dorm_id=dorm_id)
    recent_tenants = recent_tenants.select_related("dorm", "tenant_user").order_by("dorm__name", "room_number")[:6]

    context = {
        "total_dorms": total_dorms,
        "total_rooms": total_rooms,
        "count_vacant": count_vacant,
        "count_occupied": count_occupied,
        "by_dorm_labels": json.dumps(by_dorm_labels, ensure_ascii=False),
        "by_dorm_counts": json.dumps(by_dorm_counts),
        "current_dorm": current_dorm,
        "all_dorms": list(all_dorms),
        "current_month": current_month,
        "monthly_income": monthly_income,
        "outstanding_amount": outstanding_amount,
        "pending_amount": pending_amount,
        "count_paid_bills": len(paid_bills),
        "count_unpaid_bills": len(unpaid_bills),
        "count_pending_bills": len(pending_bills),
        "count_tenants": room_qs.filter(tenant_user__isnull=False).count(),
        "recent_bills": recent_bills,
        "recent_tenants": recent_tenants,
    }
    return render(request, "dashboard/index.html", context)

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
