import logging
from django.db import models
from django.utils import timezone


loger = logging.getLogger('runlog')


class ServiceMenu(models.Model):
    """项目菜单"""
    items = models.CharField(max_length=200, default='A1', help_text='服务类型简称')
    duration = models.IntegerField(default=60, help_text='服务时长, 单位分钟')
    price = models.IntegerField(default=680, help_text='服务单价')
    currency = models.CharField(max_length=20, default='piso', help_text='计价货币')
    description = models.CharField(default=' ', blank=True, max_length=500, help_text='类型说明')

    def __str__(self):
        return '项目：{:<20}  | 时间：{} 分钟  |  价格：{} {}  |  简介：{}'.format(str(self.items), str(self.duration),
                                                                     str(self.price), str(self.currency),
                                                                     str(self.description))


class StaffInfo(models.Model):
    """员工信息"""
    name = models.CharField(max_length=100, null=False, help_text='姓名')
    entry_date = models.DateField(null=True, blank=True, help_text="入职时间")
    work_status = models.IntegerField(default=1, help_text='在职状态： 1-在职， 0-离职， 2-长假')
    birthday = models.DateField(null=True, blank=True, help_text='生日')
    salary = models.IntegerField(default=0, help_text='日薪资，敏感信息可不录入')
    commission = models.IntegerField(default=60, help_text='任务提成')
    overtime_pay = models.IntegerField(default=0, null=True, help_text='加班费,时薪的两倍，单位小时')
    daily_allowance = models.IntegerField(default=0, help_text='日常补助， 如交通补助')
    half_month_payment = models.IntegerField(default=0, help_text="停车费、油费等")
    resignation = models.DateField(null=True, blank=True, help_text="离职时间")
    note = models.CharField(max_length=500, default='_', help_text='备注')

    def __str__(self):
        return '员工：{} |备注：{}'.format(self.name, self.note)

    def countslary(self, workday=13, overtime=0, commission_count=0, penalty=0):
        """计算发放工资  ; workday: 工作时间， 每半个月发一次工资！; overtime: 加班时间; penalty: 预支或迟到早退等原因扣钱"""
        total_money = (self.salary + self.daily_allowance) * workday + self.commission * commission_count
        total_money += self.overtime_pay * overtime + self.half_month_payment - penalty
        loger.info("""计算 {} 工资， 详情: (基础时薪资 {} + 交通补助{} ) * 工作天数 {} 
                    +  任务提成 {} * 提成个数 {} 
                    + 加班时薪{} * 加班时长{} 
                    + 半月应付油费 {} 
                    - 应扣款项(预支\罚金) 
                    = Total: {}""".format(self.name, self.salary, self.daily_allowance, workday, self.commission,
                                          commission_count, self.overtime_pay, overtime, self.half_month_payment,
                                          penalty, total_money))
        return total_money


class SalaryRecord(models.Model):
    """工资发放记录"""
    name = models.ForeignKey(StaffInfo, null=True, blank=True, on_delete=models.SET_NULL, help_text='员工信息关联StaffInfo表')
    work_period = models.CharField(default='_', null=False, max_length=20, help_text='计算日期区间, 如20190101 - 20190115')
    work_day = models.CharField(default='_', null=True, max_length=20, help_text='上班日期')
    work_day_count = models.IntegerField(default=0, null=False, help_text='上班天数')
    commission_count = models.IntegerField(default=0, null=False, help_text='提成个数')
    advance = models.IntegerField(default=0, null=False, help_text='预支金额')
    advance_detail = models.CharField(default='', null=True, max_length=1000, help_text='预支详情记录')
    other_money = models.IntegerField(default=0, null=False, help_text='其他补助、应发')
    total_money = models.IntegerField(default=0, null=False, help_text='应发工资')
    actual_money = models.IntegerField(default=0, null=False, help_text='发薪日实发工资')
    s_note = models.CharField(null=True, blank=True, max_length=2000, help_text='备注')

    def __str__(self):
        return 'SalaryRecord: {}'.format(self.name)


class CustomerInfo(models.Model):
    """顾客信息"""
    name = models.CharField(max_length=100, null=False, blank=True, help_text="姓名, 不唯一多个名称用'|'隔开")
    phone = models.CharField(max_length=20, default='_', help_text="电话号码(唯一)")
    address = models.TextField(max_length=500, default='_', help_text="登记地址, 多个地址以'|'隔开")
    service_times = models.IntegerField(default=0, help_text="服务次数")
    total_cost = models.IntegerField(default=0, help_text="总共消费")
    blance = models.IntegerField(default=0, help_text="充值余额")
    blance_changedate = models.DateField(null=True, help_text="余额更新日期")
    note = models.CharField(max_length=500, help_text="备注信息")

    def __str__(self):
        return 'CustomerInfo: {}'.format(self.phone)


class Massage(models.Model):
    """massage order detail"""
    # 可选支付方式
    payment_choice = (
        ('比索现金', '比索现金'),
        ('美元现金', '美元现金'),
        ('人民币现金', '人民币现金'),
        ('在线支付', '在线支付'),
    )
    order_status_options = (
        ('完成|未迟到', '完成|未迟到'),
        ('完成|迟到', '完成|迟到'),
        ('用户取消', '用户取消'),
        ('迟到取消', '迟到取消'),
    )
    name = models.CharField(max_length=200, default='_', help_text='用户姓名')
    uin = models.ForeignKey(CustomerInfo, on_delete=models.SET_NULL, related_name='customer_set', null=True, blank=True,
                            help_text='用户ID 标识符号，关联CustomerInfo， 对新用户，可为空')
    phone = models.CharField(max_length=20, default='_', help_text="电话号码")
    address = models.TextField(max_length=500, default='_', help_text="登记地址")
    service_date = models.DateField(null=True, blank=True, help_text="服务时间，以工作日为准")
    service_type = models.ForeignKey(ServiceMenu, null=True, on_delete=models.SET_NULL, help_text='服务类型')
    payment_option = models.CharField(choices=payment_choice, max_length=200, default='比索现金', help_text='付款方式')
    amount = models.IntegerField(default=0, help_text='实收金额')
    discount = models.IntegerField(default=0, help_text='优惠金额')
    massagist = models.ForeignKey(StaffInfo, on_delete=models.SET_NULL, related_name='massagist_set', null=True, blank=True,
                                  help_text='按摩师')
    tip = models.IntegerField(default=0, help_text='收取小费')
    fee = models.IntegerField(default=0, help_text='其他花费，如打车费用')
    order_status = models.CharField(choices=order_status_options, max_length=200, default='完成|未迟到', help_text='完成状态')
    note = models.CharField(default='-', blank=True, max_length=500, help_text="备注")

    def __str__(self):
        return '顾客： {} |- 消费：{}'.format(str(self.name), str(self.service_type))
