from django.conf.urls import url

from . import views

app_name = 'management_url_site'
urlpatterns = [
    url(r'^/$', views.index, name='management_index'),

]
