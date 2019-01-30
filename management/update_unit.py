import datetime
import logging
from django.db.models import Avg, Count, Min, Sum, Q
from .models import Massage
from .models import ServiceMenu
from .models import RealUser
from .models import StaffInfo
from .models import CustomerInfo
from .query_unit import *

loger = logging.getLogger('runlog')


def user_recalculate(pk):
    user = RealUser.objects.get(pk=pk)
    m_list = massage_belong_realuser(pk)
    user.total_cost = m_list.aggregate(Sum('amount'))['amount__sum']
    user.service_times = len(m_list)
    user.gifts_times = user.service_times // 10  # 消费10 次赠送一次，规则固定不变
    user.save()
    loger.info('user_recalculate 更新user pk={}，'.format(pk) +
               'total_cost={}， service_times={}， gifts_times={}'.format(user.total_cost, user.service_times,
                                                                        user.gifts_times))

