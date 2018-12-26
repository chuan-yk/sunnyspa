from django.shortcuts import render, redirect
from .models import ServiceMenu, StaffInfo, SalaryRecord
# from .forms import OrderForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    orders = ServiceMenu.objects.all()
    return render(request, 'management/index.html', {'orders': orders})