from django.forms import ModelForm
from django import forms
from .models import Massage


class MassageForm(ModelForm):
    payment_choice = (
        ('比索现金', '比索现金'),
        ('美元现金', '美元现金'),
        ('人民币现金', '人民币现金'),
        ('在线支付1', '在线支付1'),
    )
    order_status_options = (
        ('完成|未迟到', '完成|未迟到'),
        ('完成|迟到', '完成|迟到'),
        ('用户取消', '用户取消'),
        ('取消|迟到', '取消|迟到'),
    )

    order_status = forms.TypedChoiceField(required=False, choices=order_status_options, widget=forms.RadioSelect)
    # payment_option = forms.ChoiceField(choices=payment_choice)

    class Meta:
        model = Massage
        # fields = '__all__'
        fields = ['name', 'uin', 'phone', 'address', 'service_date', 'service_type', 'payment_option', 'amount',
                  'discount', 'massagist', 'tip', 'fee', 'order_status', 'note']
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'})}  # 修改template input字段类型
