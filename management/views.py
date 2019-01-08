import logging


from django.shortcuts import render, redirect
from .models import ServiceMenu, StaffInfo, SalaryRecord
# from .forms import OrderForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import F
from django.db.models import Sum


from .models import Massage
from .models import ServiceMenu


loger = logging.getLogger('runlog')


@login_required
def index(request):
    current_year = timezone.now().year
    current_month = timezone.now().month
    orders = Massage.objects.filter(service_date__year=current_year, service_date__month=current_month)
    orders_count = orders.count()
    orders_sum =
    loger.debug('current month {} have {} orders '.format(current_month, orders.count()))
    return render(request, 'index.html', {'orders': orders})
