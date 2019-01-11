from django.conf.urls import url

from . import views

app_name = 'management_url_site'
urlpatterns = [
    url(r'^$', views.index, name='home'),
    url('index', views.index, name="home_index"),
    url(r'orders/', views.ordersindex, name='orders'),
]
