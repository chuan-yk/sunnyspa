import logging
import datetime
import xlrd

from django.shortcuts import render, redirect, reverse, HttpResponse
from .models import ServiceMenu, StaffInfo, SalaryRecord
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Avg, Count, Min, Sum

from .models import Massage
from .models import ServiceMenu
from .models import CustomerInfo
from .forms import MassageAddForm, MassageEditForm

loger = logging.getLogger('runlog')
current_year = timezone.now().year
current_month = timezone.now().month


@login_required
def index(request):
    """首页"""
    orders = Massage.objects.filter(service_date__year=current_year, service_date__month=current_month)
    content = orders.aggregate(Sum('amount'), Count('pk'), )
    person_list = orders.values('uin').annotate(Count('uin'))
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
    # 返回结果计数
    orders_count = len(orders)
    # 性能控制，截断默认返回值数据量
    if len(orders) >= 150:
        orders = orders[:150]
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
            form = MassageEditForm(request.POST, instance=order)
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
        form = MassageEditForm(instance=order)
        return render(request, 'management/edit.html', {'form': form})


def related_to_customerinfo(m):
    if m.phone.strip() == '':  # 记录数据无电话号码，新增CustomerInfo记录随机值
        cif = CustomerInfo.objects.create(name=m.name, address=m.address, )
    else:
        cif, ifcreated = CustomerInfo.objects.get_or_create(phone=m.phone, name=m.name, defaults={'address': m.address})
    cif.service_times += 1
    cif.total_cost += m.amount
    cif.save()
    m.uin = cif
    return m


@login_required
def ordernew(request):
    """新增订单页面"""
    # POST 响应
    if request.POST:
        try:
            form = MassageAddForm(request.POST)
            if form.is_valid():
                m = form.save(commit=False)
                m = related_to_customerinfo(m)
                try:
                    m.save()
                    return redirect('/orders', messages.success(request, '更新订单成功', 'alert-success'))
                except Exception as e:
                    loger.error('func ordernew, add order save error. reason: {}'.format(e))
                    return redirect('/orders', messages.error(request, '更新订单失败', 'alert-danger'))
            else:
                loger.error('func ordernew, error reason : form.is_valid {}'.format(form.is_valid()))
                return redirect('/orders', messages.error(request, '输入数据格式不正确', 'alert-danger'))
        except Exception as e:
            loger.error('func ordernew try Save POST form Error , reason: {}'.format(e))
            return redirect('/orders', messages.error(request, '内部错误', 'alert-danger'))
    # GET响应
    else:
        form = MassageAddForm()
        return render(request, 'management/new.html', {'form': form})


@login_required
def orderbatchnew(request):
    """批量导入"""
    today = datetime.date.today()
    dfts_date = today.replace(day=1).strftime('%Y-%m-%d')
    dfte_date = last_day_of_month(today).strftime('%Y-%m-%d')
    content = {'dfts_date': dfts_date, 'dfte_date': dfte_date}
    if request.POST:
        if request.method == 'POST':
            # 上传附加参数获取
            timelimit = request.FILES.get('timelimit')
            if timelimit:
                dfts_date = datetime.datetime.strptime(request.FILES.get('dfts_date'), "%Y-%m-%d")
                dfte_date = datetime.datetime.strptime(request.FILES.get('dfte_date'), "%Y-%m-%d")
            ignoreerr = request.FILES.get('ignoreerr')
            try:
                the_file = request.FILES.get('thefile')
                print('==', type(the_file))
                wb = xlrd.open_workbook(filename=None, file_contents=the_file.read(), formatting_info=True)   # xls文件
                table = wb.sheets()[0]
                print('-----', table.nrows)
                print('table table.row_values(1)', table.row_values(1))
                print('table table.row_values(2)', table.row_values(2))
                print('table table.row_values(3)', table.row_values(3))
                paper_name = table.cell_value(0, 1)
                section_count = table.cell_value(1, 1)
                nrows = table.nrows  # 行数
                ncole = table.ncols  # 列数
                sec_start_line = 3
                sec_end_line = sec_start_line + int(section_count)
                for x in range(sec_start_line, sec_end_line):
                    print(table.cell_value(x, 1))
                # 用完记得删除
                wb.release_resources()
                del wb
            except:
                messages.success(request, '导入失败，try', 'alert-danger')
                return render(request, 'management/fileupload.html', content)
        print('test--------')
        messages.success(request, '导入成功', 'alert-success')
        return redirect(reverse('management_url_site:batch_add', ))
    else:
        return render(request, 'management/fileupload.html', content)


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
    loger.info("func  handler_query url: orders|analysis query_conditions : {}".format(query_conditions))
    loger.debug("func  handler_query analysis query_dict : {}".format(query_dict))
    # select对应下拉框列表
    massagist_list = StaffInfo.objects.all().values_list('name', flat=True)
    payment_list = Massage.objects.all().values_list("payment_option", flat=True).distinct().order_by()
    items_list = Massage.objects.all().values_list("service_type__items", flat=True).distinct().order_by()
    duration_list = Massage.objects.all().values_list("service_type__duration", flat=True).distinct().order_by()
    order_status_list = Massage.objects.all().values_list("order_status", flat=True).distinct().order_by()
    loger.debug("func  handler_query url: orders|analysis massagist_list: {},".format(massagist_list, ) +
                "payment_list: {}, ".format(payment_list, ) + "items_list:{}, ".format(items_list) +
                "duration_list: {}, order_status_list: {}".format(duration_list, order_status_list))
    return {'query_dict': query_dict, 'query_conditions': query_conditions, 'massagist_list': massagist_list,
            'payment_list': payment_list, 'items_list': items_list, 'duration_list': duration_list,
            'order_status_list': order_status_list, }


def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    return next_month - datetime.timedelta(days=next_month.day)


def get_months(start_date, end_date):
    """接收日期参数datetime.date, 返回月份对应区间字典"""
    months = dict()
    loger.info("func get_months 分割获取月份列表， {} -- {}".format(start_date, end_date))
    while start_date <= end_date:
        last_day_of_start_month = last_day_of_month(start_date)
        if last_day_of_start_month < end_date:
            months['{}'.format(start_date.strftime('%Y-%m'))] = {'start_date': start_date,
                                                                 'end_date': last_day_of_start_month}
        else:
            months['{}'.format(start_date.strftime('%Y-%m'))] = {'start_date': start_date,
                                                                 'end_date': end_date}
        start_date = last_day_of_start_month + datetime.timedelta(days=1)
    return months


def unit_query_staff(start_date, end_date, *additional_condition):
    """指定时间参数，不定参数Q列表， 返回员工列表"""
    filter_condition = [Q(service_date__gte=start_date), Q(service_date__lte=end_date), ] + list(additional_condition)
    loger.debug("function unit_query_staff, parameter: {}, {} ; filter_condition: {} .".format(start_date, end_date,
                                                                                               filter_condition))
    return Massage.objects.values_list('massagist__name', flat=True).filter(*filter_condition).distinct()


def unit_query_sums(start_date, end_date, *additional_condition):
    """指定时间参数，补充查询条件， 查询 amount commission tip pk"""
    filter_condition = [Q(service_date__gte=start_date), Q(service_date__lte=end_date), ] + list(additional_condition)
    loger.debug("function unit_query_sums, parameter: {}, {} ; filter_condition: {} .".format(start_date, end_date,
                                                                                               filter_condition))
    return Massage.objects.filter(*filter_condition).aggregate(Sum('amount'), Sum('commission'), Sum('tip'),
                                                               Count('pk'))


def unit_query_cus_count(start_date, end_date, *additional_condition):
    """指定时间参数，不定参数Q列表， 查询用户去重计数"""
    filter_condition = [Q(service_date__gte=start_date), Q(service_date__lte=end_date), ] + list(additional_condition)
    loger.debug("function unit_query_cus_count, parameter: {}, {} ; filter_condition: {} .".format(start_date, end_date,
                                                                                                   filter_condition))
    # 对name phone去重计次，以 phone__count 记录个体消费次数计数
    ods_with_ct = Massage.objects.filter(*filter_condition).values('name', 'phone').distinct().annotate(Count('phone'))
    # 顾客个体计数 {'name__count': ？}
    dict1 = ods_with_ct.aggregate(Count('name'))
    # 消费3次以上顾客个体计数
    dict2 = ods_with_ct.filter(Q(phone__count__gte=3)).aggregate(Count('phone__count'))
    return {**dict1, **dict2}


def unit_query_achievement(start_date, end_date, *additional_condition):
    """指定时间参数， 不定参数Q列表， 查询amount commission tip pk 和户去重计数"""
    filter_condition = [Q(service_date__gte=start_date), Q(service_date__lte=end_date), ] + list(additional_condition)
    loger.debug("function unit_query_achievement, parameter: {}, {};".format(start_date, end_date) +
                "filter_condition: {} .".format(filter_condition))
    # 总收入amount__sum， 总提成数commission__sum， 小费总数tip__sum， 订单数pk__count
    dict1 = unit_query_sums(start_date, end_date, *additional_condition)
    # 总人数name__count
    dict2 = unit_query_cus_count(start_date, end_date, *additional_condition)
    loger.debug("unit_query_performance, staff {}: ".format(additional_condition) +
                "总收入, 总提成数, 小费总数, 订单数 {} ; 总人数 {}".format(dict1, dict2))
    return {**dict1, **dict2}


def unit_query_staff_performance(start_date, end_date, *additional_condition):
    """指定时间参数， 不定参数Q列表， 返回订单统计字典数据"""
    staff_list = unit_query_staff(start_date, end_date, *additional_condition)
    staff_dict = dict()
    for staff in staff_list:
        additional_condition_2 = list(additional_condition)
        additional_condition_2.append(Q(massagist__name=staff))
        staff_dict[staff] = unit_query_achievement(start_date, end_date, *additional_condition_2)
    return {'staff_dict': staff_dict}


def unit_query_customer(start_date, end_date, *additional_condition):
    """指定时间参数，不定参数Q列表， 返回订单统计字典数据"""
    filter_condition = [Q(service_date__gte=start_date), Q(service_date__lte=end_date), ] + list(additional_condition)
    orders = Massage.objects.filter(*filter_condition)
    customer_list = orders.values('name', 'phone', 'uin__address').annotate(Count('phone'), Sum('amount'), Sum('tip'),
                                                                            Sum('discount'), Sum('fee'))
    customer_list = customer_list.order_by('-phone__count')[:5]
    return {'customer_list': customer_list, }


# combine = lambda dt: dt.update(unit_query(dt['start_date'], dt['end_date'])) or dt
def combine(dt, func, *ad):
    dt.update(func(dt['start_date'], dt['end_date'], *list(ad)))
    return dt


def combine_unit_data(summary, func, *additional_condition):
    summary['all'] = combine(summary['all'], func, *additional_condition)
    for month in summary['months']:
        summary['months'][month] = combine(summary['months'][month], func, *additional_condition)
    return summary


def multiple_query(sdate, edate, query_conditions):
    """接收日期参数, 格式‘%Y-%m-%d’，按月返回每月区间数据"""
    sdate_list, edate_list = list(map(int, sdate.split('-'))), list(map(int, edate.split('-')))
    start_date, end_date = datetime.date(*sdate_list), datetime.date(*edate_list)
    months = get_months(start_date, end_date)
    # 全部数据、每月数据
    summary = {'all': {'start_date': start_date, 'end_date': end_date}, 'months': months, }
    # 更新时间段业绩数据
    loger.info("func multiple_query 更新各时间段业绩数据")
    ad_ach = query_conditions
    ad_ach.append(Q(order_status__contains="完成"))   # 补充查询条件状态为完成
    summary = combine_unit_data(summary, unit_query_achievement, *ad_ach)
    # 更新时间顾客数据
    loger.info("func multiple_query 更新各时间段顾客数据")
    summary = combine_unit_data(summary, unit_query_customer, *query_conditions)
    # 更新时间员工数据
    loger.info("func multiple_query 更新各时间段员工数据")
    summary = combine_unit_data(summary, unit_query_staff_performance, *query_conditions)
    loger.debug("func interval_query analysis result: {}".format(summary))
    loger.info("订单统计 func multiple_query 更新数据完成")
    return summary


@login_required
def ordersanalysis(request):
    """服务订单分析"""
    handler_query_result = handler_query(request)
    orders = Massage.objects.filter(*handler_query_result['query_conditions'])
    loger.info("func ordersanalysis, query orders count: {} result id : {}".format(len(orders),
                                                                                   orders.values_list('pk', flat=True)))
    summary = multiple_query(handler_query_result['query_dict']['start_date'],
                             handler_query_result['query_dict']['end_date'],
                             handler_query_result['query_conditions'], )
    print(summary)
    # template - content
    content = {'massagist_list': handler_query_result['massagist_list'],
               'payment_list': handler_query_result['payment_list'],
               'items_list': handler_query_result['items_list'],
               'duration_list': handler_query_result['duration_list'],
               'order_status_list': handler_query_result['order_status_list'],
               **handler_query_result['query_dict'],
               **summary, }
    return render(request, 'management/analysis.html', content)
