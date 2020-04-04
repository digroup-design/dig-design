from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from . import views

#TODO: Figure out how to allow spaces in URL

address = 'address=<slug:address>'
apn = 'apn=<slug:apn>'
city = 'city=<slug:city>'
state = 'state=<slug:state>'

urlpatterns = [
    path('', views.home, name='reports-home'),
    path('reports/api/{0}'.format('&'.join([address, city, state])), views.send_json),
    path('reports/api/{0}'.format('&'.join([apn, city, state])), views.send_json),
    path('reports/api/{0}'.format('&'.join([apn])), views.send_json),
    path('reports/api/{0}'.format('&'.join([address])), views.send_json),
    path('about/', views.about, name='reports-about'),
]