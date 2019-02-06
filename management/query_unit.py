import datetime
import logging
from django.db.models import Avg, Count, Min, Sum, Q
from .models import Massage
from .models import ServiceMenu
from .models import RealUser
from .models import StaffInfo
from .models import CustomerInfo

loger = logging.getLogger('runlog')


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
    ad_ach.append(Q(order_status__contains="完成"))  # 补充查询条件状态为完成
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


def handler_query(request):
    """复用方法, 返回值： {'query_dict': 查询条件， 'query_conditions': 合并后的Q实例, 'select_list': select_list} """
    query_dict = {'name': '', 'exact_name': '', 'phone': '', 'address': '', 'note': '', 'massagist': '', 'payment': '',
                  'items': '', 'duration': '', 'order_status': '', 'fee': '', 'balance': '', 'discount': '',
                  'start_date': '', 'end_date': '', }
    # 查询条件开始日期
    if request.GET.get('start_date'):
        start_date = datetime.datetime.strptime(request.GET['start_date'].strip(), '%Y-%m-%d').date()
    else:
        start_date = datetime.date(2017, 1, 1)  # 默认开业时间
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
    if request.GET.get('balance'):
        balance_num = request.GET['balance'].strip()
        if balance_num == 1:
            query_conditions.append(Q(uin__balance__gt=0))
        elif balance_num == 0:
            query_conditions.append(Q(uin__balance__exact=0))
        else:
            pass
        query_dict['balance'] = balance_num
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


def cus_handle_query(request):
    # 顾客查询条件解析
    query_dict = {'name': '', 'exact_name': '', 'phone': '', 'address': '', 'note': '', }
    query_conditions = []
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
    return {'query_dict': query_dict, 'query_conditions': query_conditions, }


def massage_belong_realuser(pk):
    """realuser 关联cus下全部massage"""
    return Massage.objects.filter(Q(uin__user__pk=pk), ~Q(amount=0))


def massage_set_sum(m_set):
    """amount 求和"""
    return m_set.aggregate(Sum('amount'))

