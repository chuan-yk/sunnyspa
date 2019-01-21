from django.contrib import admin


from .models import ServiceMenu
from .models import StaffInfo
from .models import SalaryRecord
from .models import CustomerInfo
from .models import RealUser
from .models import Massage


admin.site.register(ServiceMenu)
admin.site.register(StaffInfo)
admin.site.register(SalaryRecord)
admin.site.register(RealUser)
admin.site.register(CustomerInfo)
admin.site.register(Massage)
