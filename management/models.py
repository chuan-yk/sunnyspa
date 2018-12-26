from django.db import models
from django.utils import timezone
from sunnyspa.settings import loger


class ServiceMenu(models.Model):
    """项目菜单"""
    items = models.CharField(max_length=200, default='A1', help_text='服务类型简称')
    duration = models.IntegerField(default=60, help_text='服务时长, 单位分钟')
    price = models.IntegerField(default=680, help_text='服务单价')
    Currency = models.CharField(max_length=20, default='piso', help_text='计价货币')

    def __str__(self):
        return '{}:{}'.format(str(self.items), str(self.duration))


class StaffInfo(models.Model):
    """员工信息"""
    name = models.CharField(max_length=100, null=False, help_text='姓名')
    entry_date = models.DateField(null=True, help_text="入职时间")
    work_status = models.IntegerField(default=1, help_text='在职状态： 1-在职， 0-离职， 2-长假')
    birthday = models.DateField(null=True, help_text='生日')
    salary = models.IntegerField(default=0, help_text='日薪资，敏感信息可不录入')
    commission = models.IntegerField(default=60, help_text='任务提成')
    overtime_pay = models.IntegerField(default=0, null=True, help_text='加班费,时薪的两倍，单位小时')
    daily_allowance = models.IntegerField(default=0, help_text='日常补助， 如交通补助')
    half_month_payment = models.IntegerField(default=0, help_text="停车费、油费等")
    resignation = models.DateField(null=True, help_text="离职时间")
    note = models.CharField(max_length=500, default='_', help_text='备注')

    def __str__(self):
        return self.name

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
    name = models.ForeignKey(StaffInfo, null=True, on_delete=models.SET_NULL, help_text='员工信息关联StaffInfo表')
    work_period = models.CharField(default='_', null=False, max_length=20, help_text='计算日期区间')
    work_day = models.CharField(default='_', null=True, max_length=20, help_text='上班日期')
    work_day_count = models.IntegerField(default=0, null=False, help_text='上班天数')
    commission_count = models.IntegerField(default=0, null=False, help_text='提成个数')
    advance = models.IntegerField(default=0, null=False, help_text='预支金额')
    advance_detail = models.CharField(default='', null=True, max_length=1000, help_text='预支详情记录')
    other_money = models.IntegerField(default=0, null=False, help_text='其他补助、应发')
    total_money = models.IntegerField(default=0, null=False, help_text='应发工资')
    actual_money = models.IntegerField(default=0, null=False, help_text='发薪日实发工资')
    s_note = models.CharField(null=True, max_length=2000, help_text='备注')

