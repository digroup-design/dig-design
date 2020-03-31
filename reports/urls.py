from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from . import views

address = 'address=<slug:address>'
apn = 'apn=<slug:apn>'
city = 'city=<slug:city>'
state = 'state=<slug:state>'

urlpatterns = [
    path('', views.home, name='reports-home'),
    path('reports/api/' + '&'.join([address, city, state]), views.send_json),
    path('reports/api/' + '&'.join([apn, city, state]), views.send_json),
    path('reports/api/' + '&'.join([apn]), views.send_json),
    path('reports/api/' + '&'.join([address]), views.send_json),
    path('about/', views.about, name='reports-about'),
]
