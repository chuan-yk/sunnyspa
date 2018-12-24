from django.db import models
from django.utils import timezone


class Message(models):
    """message order detail"""
    name = models.CharField(max_length=200, default='_', help_text='用户姓名')
    uin = models.IntegerField(default=0)
    phone = models.CharField(max_length=20, default='_', help_text="电话号码")
    address = models.TextField(max_length=500, default='_', help_text="登记地址")
    service_date = models.DateField(default=timezone.now(), help_text="服务时间，以工作日为准")
    service_id = models.TextField()
    payment_option = models.CharField(max_length=50)
    amount = models.IntegerField()
    order_status = models.CharField(max_length=50)

    def __str__(self):
        return str(self.name) + str(self.service_id)