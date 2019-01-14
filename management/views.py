import logging
import datetime


from django.shortcuts import render, redirect, HttpResponse
from .models import ServiceMenu, StaffInfo, SalaryRecord
# from .forms import OrderForm
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Avg, Count, Min, Sum


from .models import Massage
from .models import ServiceMenu
from .forms import MassageForm

loger = logging.getLogger('runlog')
current_year = timezone.now().year
current_month = timezone.now().month


@login_required
def index(request):
    """首页"""
    orders = Massage.objects.filter(service_date__year=current_year, service_date__month=current_month)
    content = orders.aggregate(Sum('amount'), Count('pk'), )
    person_list = orders.values('phone', 'name').annotate(Count('phone'))
    person_count = len(person_list)
    current_income = sum(orders.values_list('amount', flat=True))
    loger.debug('current month {} have {} orders, toal amount = {}  '.format(current_month, content['pk__count'],
                                                                             content['amount__sum']))
    return render(request, 'management/index.html',
                  {'content': content, 'person_count': person_count, 'current_income': current_income})


@login_required
def ordersindex(request):
    """订单页"""
    orders = Massage.objects.all().order_by('-pk')[:100]
    return render(request, 'management/ordersindex.html', {'orders': orders})


@login_required
def orderedit(request, pk):
    """订单修改页面"""
    order = Massage.objects.get(id=pk)
    # POST 响应
    if request.POST:
        try:
            form = MassageForm(request.POST, instance=order)
            if form.is_valid():
                if form.save():
                    return redirect('/orders', messages.success(request, '更新订单成功', 'alert-success'))
                else:
                    return redirect('/orders', messages.error(request, '更新订单失败', 'alert-danger'))
            else:
                loger.error(form.is_valid())
                return redirect('/orders', messages.error(request, '输入数据格式不正确', 'alert-danger'))
        except Exception as e:
            loger.error(e)
            return redirect('/orders', messages.error(request, '内部错误', 'alert-danger'))
    # GET响应
    else:
        form = MassageForm(instance=order)
        return render(request, 'management/edit.html', {'form': form})


@login_required
def ordernew(request):
    """新增订单页面"""
    # POST 响应
    if request.POST:
        try:
            form = MassageForm(request.POST)
            if form.is_valid():
                if form.save():
                    return redirect('/orders', messages.success(request, '更新订单成功', 'alert-success'))
                else:
                    return redirect('/orders', messages.error(request, '更新订单失败', 'alert-danger'))
            else:
                loger.error(form.is_valid())
                return redirect('/orders', messages.error(request, '输入数据格式不正确', 'alert-danger'))
        except Exception as e:
            loger.error(e)
            return redirect('/orders', messages.error(request, '内部错误', 'alert-danger'))
    # GET响应
    else:
        form = MassageForm()
        return render(request, 'management/edit.html', {'form': form})


@login_required
def ordersanalysis(request):
    """服务订单分析"""
    # 查询条件开始日期
    if request.GET.get('start_date'):
        start_date = datetime.datetime.strptime(request.GET['start_date']).date()
    else:
        start_date = datetime.date(2017, 8, 31)     # 默认开业时间
    # 查询条件结束日期
    if request.GET.get('end_date'):
        end_date = datetime.datetime.strptime(request.GET['end_time']).date()
    else:
        end_date = datetime.date.today()
    query_conditions = [Q(service_date__gte=start_date), Q(service_date__lte=end_date)]
    # 员工查询条件
    if request.GET.get('massagist'):
        query_conditions.append(Q(massagist__name=request.GET['massagist']))
    # 客户姓名查询条件
    if request.GET.get('name'):
        query_conditions.append(Q(name=request.GET['name']))
    # 客户电话号码查询条件
    if request.GET.get('phone'):
        query_conditions.append(Q(phone=request.GET['phone']))
    # 车费查询条件
    if request.GET.get('fee'):
        query_conditions.append(Q(fee=request.GET['fee']))
    # 类型查询
    if request.GET.get('items'):
        query_conditions.append(Q(service_type__items=request.GET['items']))
    # 时长查询
    if request.GET.get('duration'):
        query_conditions.append(Q(service_type__duration=request.GET['duration']))
    # 地址查询，模糊条件
    if request.GET.get('address'):
        query_conditions.append(Q(address__icontains=request.GET['address']))
    # 订单状态查询，模糊条件
    if request.GET.get('order_status'):
        query_conditions.append(Q(order_status__icontains=request.GET['order_status']))
    # 备注信息查询，模糊条件
    if request.GET.get('note'):
        query_conditions.append(Q(note__icontains=request.GET['note']))
    loger.info("ordersanalysis query_conditions : {}".format(query_conditions))
    orders = Massage.objects.filter(*query_conditions)
    loger.info("ordersanalysis, query oders count: {} result id : {}".format(len(orders), orders.values_list('pk', flat=True)))
    content = orders.aggregate(Sum('amount'), Count('pk'), )
    person_list = orders.values('phone', 'name').annotate(Count('phone'))
    person_count = len(person_list)
    current_income = sum(orders.values_list('amount', flat=True))
    loger.debug('current month {} have {} orders, toal amount = {}  '.format(current_month, content['pk__count'],
                                                                             content['amount__sum']))
    #return render(request, 'management/index.html',
    #              {'content': content, 'person_count': person_count, 'current_income': current_income})
    return HttpResponse('It is OK page ')
