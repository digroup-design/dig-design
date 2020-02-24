from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from . import views
#from reports.views import HomeView

urlpatterns = [
    path('', views.home, name='reports-home'),
    path('about/', views.about, name='reports-about'),
]
