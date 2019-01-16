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
    handler_query_result = handler_query(request)
    orders = Massage.objects.filter(*handler_query_result['query_conditions']).order_by('-pk')
    # 性能控制，截断默认返回值数据量
    if len(orders) >= 150:
        orders = orders[:150]
    # 返回结果计数
    orders_count = orders.count()
    content = {'massagist_list': handler_query_result['massagist_list'],
               'payment_list': handler_query_result['payment_list'],
               'items_list': handler_query_result['items_list'],
               'duration_list': handler_query_result['duration_list'], 'orders_count': orders_count,
               'order_status_list': handler_query_result['order_status_list'], 'orders': orders,
               **handler_query_result['query_dict'], }
    return render(request, 'management/ordersindex.html', content)


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


def handler_query(request):
    """复用方法, 返回值： {'query_dict': 查询条件， 'query_conditions': 合并后的Q实例, 'select_list': select_list} """
    query_dict = {'name': '', 'exact_name': '', 'phone': '', 'address': '', 'note': '', 'massagist': '', 'payment': '',
                  'items': '', 'duration': '', 'order_status': '', 'fee': '', 'blance': '', 'discount': '',
                  'start_date': '', 'end_date': '', }
    # 查询条件开始日期
    if request.GET.get('start_date'):
        start_date = datetime.datetime.strptime(request.GET['start_date'].strip(), '%Y-%m-%d').date()
    else:
        start_date = datetime.date(2017, 8, 31)  # 默认开业时间
    query_dict['start_date'] = start_date.strftime("%Y-%m-%d")
    # 查询条件结束日期
    if request.GET.get('end_date'):
        end_date = datetime.datetime.strptime(request.GET['end_date'].strip(), '%Y-%m-%d').date()
    else:
        end_date = datetime.date.today()
    query_dict['end_date'] = end_date.strftime("%Y-%m-%d")
    query_conditions = [Q(service_date__gte=start_date), Q(service_date__lte=end_date)]
    # 客户姓名查询条件, 精准查询
    if request.GET.get('exact_name'):
        exact_name = request.GET['exact_name'].strip()
        if exact_name:  # 排除''
            query_conditions.append(Q(name__exact=exact_name))
            query_dict['exact_name'] = exact_name
    # 客户姓名查询条件, 模糊查询
    if request.GET.get('name'):
        name = request.GET['name'].strip()
        if name:  # 排除''
            query_conditions.append(Q(name__icontains=name))
            query_dict['name'] = name
    # 客户电话号码查询条件, 模糊查询
    if request.GET.get('phone'):
        phone = request.GET['phone'].strip()
        if phone:  # 排除''
            query_conditions.append(Q(phone__icontains=phone))
            query_dict['phone'] = phone
    # 地址查询，模糊条件
    if request.GET.get('address'):
        address = request.GET['address'].strip()
        if address:
            query_conditions.append(Q(address__icontains=address))
            query_dict['address'] = address
    # 备注信息查询，模糊条件
    if request.GET.get('note'):
        note = request.GET['note'].strip()
        if note:
            query_conditions.append(Q(note__icontains=note))
            query_dict['note'] = note
    # 员工查询条件
    if request.GET.get('massagist'):
        massagist = request.GET['massagist'].strip()
        query_conditions.append(Q(massagist__name=massagist))
        query_dict['massagist'] = massagist
    # 支付方式查询
    if request.GET.get('payment'):
        payment = request.GET['payment'].strip()
        query_conditions.append(Q(payment_option=payment))
        query_dict['payment'] = payment
    # 类型查询
    if request.GET.get('items'):
        items = request.GET['items'].strip()
        query_conditions.append(Q(service_type__items=items))
        query_dict['items'] = items
    # 时长查询
    if request.GET.get('duration'):
        duration = request.GET['duration'].strip()
        query_conditions.append(Q(service_type__duration=duration))
        try:
            query_dict['duration'] = int(duration)
        except:
            query_dict['duration'] = duration
    # 订单状态查询，模糊条件
    if request.GET.get('order_status'):
        order_status = request.GET['order_status'].strip()
        query_conditions.append(Q(order_status__icontains=order_status))
        query_dict['order_status'] = order_status
    # 车费查询条件
    if request.GET.get('fee'):
        fee_value = request.GET['fee'].strip()
        if fee_value == '1':
            query_conditions.append(Q(fee__gt=0))
        elif fee_value == '0':
            query_conditions.append(Q(fee__exact=0))
        else:
            pass
        query_dict['fee'] = fee_value
    # 用户余额有无查询
    if request.GET.get('blance'):
        blance_num = request.GET['blance'].strip()
        if blance_num == 1:
            query_conditions.append(Q(uin__blance__gt=0))
        elif blance_num == 0:
            query_conditions.append(Q(uin__blance__exact=0))
        else:
            pass
        query_dict['blance'] = blance_num
    # 是否打折条件查询
    if request.GET.get('discount'):
        discount_tag = request.GET['discount']
        if discount_tag == 1:
            query_conditions.append(Q(discount__gt=0))
        elif discount_tag == 0:
            query_conditions.append(Q(discount__exact=0))
        else:
            pass
        query_dict['discount'] = discount_tag
    loger.debug("func  handler_query analysis query_conditions : {}".format(query_conditions))
    loger.debug("func  handler_query analysis query_dict : {}".format(query_dict))
    # select对应下拉框列表
    massagist_list = StaffInfo.objects.all().values_list('name', flat=True)
    payment_list = Massage.objects.all().values_list("payment_option", flat=True).distinct().order_by()
    items_list = Massage.objects.all().values_list("service_type__items", flat=True).distinct().order_by()
    duration_list = Massage.objects.all().values_list("service_type__duration", flat=True).distinct().order_by()
    order_status_list = Massage.objects.all().values_list("order_status", flat=True).distinct().order_by()
    loger.debug("""func  handler_query analysis massagist_list: {}, payment_list: {}, items_list:{}, duration_list: {}, order_status_list: {}""".format(
            massagist_list, payment_list, items_list, duration_list, order_status_list))
    return {'query_dict': query_dict, 'query_conditions': query_conditions, 'massagist_list': massagist_list,
            'payment_list': payment_list, 'items_list': items_list, 'duration_list': duration_list,
            'order_status_list': order_status_list, }


@login_required
def ordersanalysis(request):
    """服务订单分析"""
    handler_query_result = handler_query(request)
    orders = Massage.objects.filter(*handler_query_result['query_conditions'])
    loger.info("func ordersanalysis, query orders count: {} result id : {}".format(len(orders),
                                                                                   orders.values_list('pk', flat=True)))
    sum_count = orders.aggregate(Sum('amount'), Count('pk'), )
    # template - content
    content = {'massagist_list': handler_query_result['massagist_list'],
               'payment_list': handler_query_result['payment_list'],
               'items_list': handler_query_result['items_list'],
               'duration_list': handler_query_result['duration_list'],
               'order_status_list': handler_query_result['order_status_list'],
               **handler_query_result['query_dict'], **sum_count, }
    # content = {'massagist_list': massagist_list, 'payment_list': payment_list, 'items_list': items_list,
    #            'duration_list': duration_list, 'order_status_list': order_status_list, **query_dict, **sum_count, }
    return render(request, 'management/analysis.html', content)
