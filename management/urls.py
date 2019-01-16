from django.conf.urls import url

from . import views

app_name = 'management_url_site'
urlpatterns = [
    url(r'^$', views.index, name='home'),
    url('index$', views.index, name="home_index"),
    url(r'orders$', views.ordersindex, name='orders'),
    url(r'orders/(?P<pk>\d+)/edit$', views.orderedit, name='edit'),
    url(r'orders/add$', views.ordernew, name='add'),
    url(r'orders/batch$', views.ordernew, name='batch_add'),
    url(r'orders/analysis$', views.ordersanalysis, name='analysis'),
]
