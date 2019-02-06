import logging
import datetime
import xlrd
import uuid
from django.shortcuts import render, redirect, reverse, HttpResponse, get_object_or_404, HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Min, Sum, Q

from .models import Massage
from .models import RealUser
from .models import ServiceMenu
from .models import StaffInfo
from .models import CustomerInfo
from .forms import MassageAddForm, MassageEditForm
from .excel_import_orders import main_read, data_insert
from .query_unit import *
from .update_unit import *

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
    # 当前时间范围内的员工列表
    massagist_list = set(orders.values_list('massagist__name', flat=True).distinct())
    # 返回结果计数
    orders_count = len(orders)
    # 性能控制，截断默认返回值数据量
    if len(orders) >= 150:
        orders = orders[:150]
    content = {'massagist_list': massagist_list,
               # 'massagist_list': handler_query_result['massagist_list'],      # 默认返回全部
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
    if request.method == 'POST':
        # 上传附加参数获取
        timelimit = request.POST.get('timelimit')
        if timelimit == '1':
            dfts_date = datetime.datetime.strptime(request.POST.get('dfts_date'), "%Y-%m-%d").date()
            dfte_date = datetime.datetime.strptime(request.POST.get('dfte_date'), "%Y-%m-%d").date()
        # ignoreerr = request.POST.get('ignoreerr')
        forcecover = request.POST.get('forcecover')
        loger.debug(
            '上传文件附加条件为： timelimit={}， {}， {}， forcecover={}'.format(timelimit, dfts_date, dfte_date, forcecover))
        if forcecover == '1':
            Massage.objects.filter(Q(service_date__gte=dfts_date), Q(service_date__lte=dfte_date)).delete()
        try:
            the_file = request.FILES.get('thefile')
            wb = xlrd.open_workbook(filename=None, file_contents=the_file.read(), formatting_info=True)  # xls文件
            table = wb.sheets()[0]
            mlist = main_read(table, timelimit=timelimit, s_date=dfts_date, e_date=dfte_date)
            loger.debug('view function get mlist ==')
            insert_result = data_insert(mlist)
            if insert_result['status']:
                loger.info('request 上传文件导入成功')
            else:
                raise ValueError(insert_result['error'])
            # 用完记得删除
            wb.release_resources()
            del wb
        except Exception as e:
            loger.error('request 上传文件导入失败， 错误原因{}'.format(str(e)))
            messages.error(request, '导入失败，try', 'alert-danger')
            return render(request, 'management/fileupload.html', content)
        messages.success(request, '导入成功, 共{}条数据'.format(insert_result['num']), 'alert-success')
        return redirect(reverse('management_url_site:orders', ))
    else:
        return render(request, 'management/fileupload.html', content)


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
    # print(summary)
    # template - content
    content = {'massagist_list': handler_query_result['massagist_list'],
               'payment_list': handler_query_result['payment_list'],
               'items_list': handler_query_result['items_list'],
               'duration_list': handler_query_result['duration_list'],
               'order_status_list': handler_query_result['order_status_list'],
               **handler_query_result['query_dict'],
               **summary, }
    print('----', content['balance'])
    return render(request, 'management/analysis.html', content)


@login_required
def staff_index(request):
    return HttpResponse('it is test !')


@login_required
def staff_edit(request):
    return HttpResponse('it is test !')


@login_required
def salary(request):
    return HttpResponse('it is test !')


@login_required
def salary_recalculate(request):
    return HttpResponse('it is test !')


@login_required
def attendance(request):
    return HttpResponse('it is test !')


@login_required
def cus_info(request):
    cus_handle_query_result = cus_handle_query(request)
    query_conditions = cus_handle_query_result['query_conditions']
    query_conditions.append(~Q(isvalid=0))
    users = RealUser.objects.filter(*query_conditions)
    content = {'users': users, **cus_handle_query_result['query_dict'], }
    return render(request, 'management/cusindex.html', content)


@login_required
def cus_edit(request, pk):
    user = get_object_or_404(RealUser, pk=pk)
    if request.method == 'POST':
        try:
            user.address = request.POST.get('address').strip()
            user.balance = int(request.POST.get('balance'))
            user.feedback_times = int(request.POST.get('feedback_times'))
            user.phone_2 = request.POST.get('phone_2').strip()
            user.note = request.POST.get('note').strip()
            user.isvalid = int(request.POST.get('isvalid'))
            user.save()
            loger.debug('view function cus_edit, update {} '.format(user))
            messages.success(request, '更新成功', 'alert-success')
            return redirect(reverse('management_url_site:cus_info', ))
        except Exception as e:
            print(request.POST.get('balance'), request.POST.get('feedback_times'), request.POST.get('isvalid'))
            loger.error('view function cus_edit update {} Error: {}'.format(user, str(e)))
            messages.error(request, '更新失败', 'alert-danger')
            return redirect(reverse('management_url_site:cus_info', ))
    return render(request, 'management/cusedit.html', {'user': user})


@login_required
def cus_recalculate_all(request):
    users = RealUser.objects.filter(~Q(isvalid=0))
    for u in users:
        user_recalculate(u.pk)
    messages.success(request, '全部用户信息更新成功', 'alert-success')
    return redirect(reverse('management_url_site:cus_info', ))


@login_required
def cus_recalculate(request, pk):
    """重算Realuser 对应的统计数据"""
    user_recalculate(pk)
    messages.success(request, '顾客ID={}信息更新成功'.format(pk), 'alert-success')
    # return redirect(reverse('management_url_site:cus_info', ))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def cus_relate(request):
    if request.method == 'POST':
        cus_list = [int(i) for i in request.POST.getlist('cus_id')]
        if len(cus_list) == 0:
            messages.error(request, '左侧"订单记录用户"至少选择一个', 'alert-danger')
            return redirect(reverse('management_url_site:cus_relate', ))
        user_uuid = request.POST.get('user_uid')
        real_user = RealUser.objects.get(uuid__exact=uuid.UUID(user_uuid))      # 关联至该用户
        cus_obj_list = CustomerInfo.objects.filter(Q(pk__in=cus_list))          # 更新customer info 列表
        changed_user_pk = [real_user.pk, ]                                      # 受影响 Real user
        for i in cus_obj_list:
            changed_user_pk.append(i.user.pk)
            i.user = real_user
            i.save()
            loger.debug('view cus_relate , change Customer_info {} relate to real user {}'.format(i.pk, real_user.uuid))
        for j in changed_user_pk:
            user_recalculate(j)
        loger.debug('view cus_relate 重算 {} 顾客信息完成'.format(changed_user_pk))
        messages.success(request, '更新关联关系成功', 'alert-success')
        return redirect(reverse('management_url_site:cus_relate', ))
    else:
        cus_handle_query_result = cus_handle_query(request)
        query_conditions = cus_handle_query_result['query_conditions']
        if request.GET.get('user_uuid'):        # 指定Real user uuid
            uid = uuid.UUID(request.GET['user_uuid'].strip())
            users = RealUser.objects.filter(Q(uuid__exact=uid))
        else:
            user_query_conditions = query_conditions + [~Q(isvalid=0)]
            users = RealUser.objects.filter(*user_query_conditions)[:12]
        customers = CustomerInfo.objects.filter(*query_conditions)
        if request.GET.get('filter_h') == '1':
            customers = customers.filter(Q(user__isvalid=0))
        content = {'users': users, 'customers': customers, **cus_handle_query_result['query_dict'], }
        return render(request, 'management/cusrelationship.html', content)


@login_required
def cus_summary(request):
    handler_query_result = handler_query(request)
    # query_dict = {'name': '','exact_name': '', 'phone': '', 'address': '', 'note': '', 'massagist': '', 'payment': '',
    #               'items': '', 'duration': '', 'order_status': '', 'fee': '', 'balance': '', 'discount': '',
    #               'start_date': '', 'end_date': '', }
    query_dict = handler_query_result['query_dict']
    # Realuser 查询条件
    user_query_conditions = []
    if query_dict['name'] != '':
        user_query_conditions = user_query_conditions.append(Q(name__icontains=query_dict['name']))
    if query_dict['exact_name'] != '':
        user_query_conditions = user_query_conditions.append(Q(name__exact=query_dict['exact_name']))
    if query_dict['phone'] != '':
        user_query_conditions = user_query_conditions.append(Q(phone__icontains=query_dict['phone']))
    if query_dict['address'] != '':
        user_query_conditions = user_query_conditions.append(Q(address__icontains=query_dict['address']))
    if query_dict['note'] != '':
        user_query_conditions = user_query_conditions.append(Q(note__exact=query_dict['note']))
    # Massage 查询条件
    mg_query_conditions = []
    if query_dict['massagist'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(massagist__name=query_dict['massagist']))
    if query_dict['payment'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(payment_option=query_dict['payment']))
    if query_dict['items'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(service_type__items=query_dict['items']))
    if query_dict['duration'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(service_type__duration=query_dict['duration']))
    if query_dict['order_status'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(order_status__icontains=query_dict['order_status']))
    if query_dict['fee'] != '':
        fee_value = query_dict['fee']
        if fee_value == '1':
            mg_query_conditions.append(Q(fee__gt=0))
        elif fee_value == '0':
            mg_query_conditions.append(Q(fee__exact=0))
        else:
            pass
        mg_query_conditions = mg_query_conditions.append(Q(payment_option=query_dict['payment']))
    if query_dict['balance'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(payment_option=query_dict['payment']))
    if query_dict['discount'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(payment_option=query_dict['payment']))
    if query_dict['start_date'] != '':
        mg_query_conditions = mg_query_conditions.append(Q(payment_option=query_dict['payment']))

    if query_dict['end_date'] != '':
        pass
    user_list = RealUser.objects.filter(*user_query_conditions)

    content = {'massagist_list': handler_query_result['massagist_list'],      # 默认返回全部
               'payment_list': handler_query_result['payment_list'],
               'items_list': handler_query_result['items_list'],
               'duration_list': handler_query_result['duration_list'], 'orders_count': orders_count,
               'order_status_list': handler_query_result['order_status_list'], 'orders': orders,
               **handler_query_result['query_dict'], }
    return render(request, 'management/cussummary.html', content)

