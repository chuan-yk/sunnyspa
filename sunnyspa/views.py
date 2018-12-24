from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from massage.models import Massage

@login_required
def indexpage(request):
    orders = Massage.objects.all()
    return render(request, 'index.html', {'orders': orders})