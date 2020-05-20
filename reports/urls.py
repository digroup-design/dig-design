from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from . import views

address = 'address=<slug:address>'
apn = 'apn=<slug:apn>'
city = 'city=<slug:city>'
state = 'state=<slug:state>'

url_views = (
    ('reports/api/{0}', views.send_json),
    ('reports/csv/{0}', views.send_csv)
)

params = (
    (address, city, state),
    (apn, city, state),
    (apn,),
    (address,),
)

#TODO: Figure out how to allow spaces in URL

urlpatterns = [
    path('', views.home, name='reports-home'),
    path('about/', views.about, name='reports-about'),
]

for u in url_views:
    for p in params:
        urlpatterns.append(
            path(u[0].format('&'.join(p)), u[1])
        )