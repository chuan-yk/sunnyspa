from django.shortcuts import render, redirect
from .models import Order
# from .forms import OrderForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    orders = Order.objects.all()
    return render(request, 'management/index.html', {'orders': orders})