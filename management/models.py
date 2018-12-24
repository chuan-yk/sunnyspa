from django.db import models


class Order (models.Model):
    name = models.CharField(max_length=200, default='_', help_text='用户姓名');
