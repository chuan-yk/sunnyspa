import datetime


from django.shortcuts import render, redirect
from .models import ServiceMenu, StaffInfo, SalaryRecord
# from .forms import OrderForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import F
from django.db.models import Sum


from .models import Massage
from .models import ServiceMenu

@login_required
def index(request):
    """首页展示"""
    #orders_count = Massage.objects.filter(service_date__month=datetime.date.today().month).count()
    #income = Massage.objects.annotate(sum=F(amount)+F(tip)).aggregate(Sum(sum))
    #
    orders = {'test':'test'}

    return render(request, 'index.html', {'orders': orders})
