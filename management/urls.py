from django.conf.urls import url

from . import views

app_name = 'management_url_site'
urlpatterns = [
    url(r'^$', views.index, name='home'),
    url('index$', views.index, name="home_index"),
    url(r'orders$', views.ordersindex, name='orders'),
    url(r'orders/(?P<pk>\d+)/edit$', views.orderedit, name='edit'),
    url(r'orders/add$', views.ordernew, name='add'),
    url(r'orders/batch$', views.orderbatchnew, name='batch_add'),
    url(r'orders/analysis$', views.ordersanalysis, name='analysis'),
    url(r'staffs', views.staff_index, name='staff_index'),
    url(r'staff/edit', views.staff_edit, name='staff_edit'),
    url(r'staff/salary', views.salary, name='salary'),
    url(r'staff/salary/recalculate', views.salary_recalculate, name='salary_recalculate'),
    url(r'staff/attendance', views.attendance, name='attendance'),
    # url(r'staff/attendance/upload', views.attendance, name='attendance'),
    url(r'customerinfo', views.cus_info, name='customerinfo'),
    url(r'customerinfo/summary', views.cus_summary, name='customerinfo_summary'),
]
