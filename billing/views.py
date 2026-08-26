from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dorms.utils import is_staff_user
from .forms import BillForm, BillItemFormSet, PaymentSlipForm
from .models import Bill


def _can_access_bill(user, bill):
    return user.is_staff or user.is_superuser or bill.room.tenant_user_id == user.id


@login_required
def bill_list(request):
    bills = Bill.objects.select_related("room", "room__dorm").prefetch_related("items")
    if not (request.user.is_staff or request.user.is_superuser):
        bills = bills.filter(room__tenant_user=request.user)
    return render(request, "billing/list.html", {"bills": bills})


@user_passes_test(is_staff_user)
def bill_create(request):
    if request.method == "POST":
        form = BillForm(request.POST)
        formset = BillItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bill = form.save()
                formset.instance = bill
                formset.save()
            messages.success(request, "สร้างบิลค่าเช่าเรียบร้อยแล้ว")
            return redirect("bill_detail", pk=bill.pk)
    else:
        form = BillForm()
        formset = BillItemFormSet()
    return render(request, "billing/create.html", {"form": form, "formset": formset})


@login_required
def bill_detail(request, pk):
    bill = get_object_or_404(Bill.objects.select_related("room", "room__dorm").prefetch_related("items"), pk=pk)
    if not _can_access_bill(request.user, bill):
        messages.error(request, "คุณไม่มีสิทธิ์ดูบิลนี้")
        return redirect("bill_list")
    return render(request, "billing/detail.html", {"bill": bill, "slip_form": PaymentSlipForm(instance=bill)})


@login_required
def upload_slip(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method != "POST" or not _can_access_bill(request.user, bill):
        return redirect("bill_list")
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, "ให้ผู้เช่าส่งสลิปจากบัญชีของตน")
        return redirect("bill_detail", pk=pk)
    if bill.status != Bill.OVERDUE:
        messages.error(request, "บิลนี้ไม่อยู่ในสถานะให้ส่งสลิป")
        return redirect("bill_detail", pk=pk)
    form = PaymentSlipForm(request.POST, request.FILES, instance=bill)
    if form.is_valid() and form.cleaned_data.get("payment_slip"):
        bill = form.save(commit=False)
        bill.status = Bill.PENDING_VERIFICATION
        bill.slip_uploaded_at = timezone.now()
        bill.save()
        messages.success(request, "ส่งสลิปแล้ว รอแอดมินตรวจสอบการโอนเงิน")
    else:
        messages.error(request, "กรุณาเลือกรูปสลิป")
    return redirect("bill_detail", pk=pk)


@user_passes_test(is_staff_user)
def verify_payment(request, pk):
    bill = get_object_or_404(Bill, pk=pk)
    if request.method == "POST" and bill.status == Bill.PENDING_VERIFICATION:
        bill.status = Bill.PAID
        bill.verified_at = timezone.now()
        bill.save(update_fields=["status", "verified_at"])
        messages.success(request, "ตรวจสอบแล้ว บิลเปลี่ยนเป็นสถานะชำระเงินแล้ว")
    return redirect("bill_detail", pk=pk)
