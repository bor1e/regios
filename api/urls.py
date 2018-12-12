from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    # 127.0.0.1:8000/api/
    path('multiple', views.multiple, name='multiple'),
    path('post/', views.post, name='post'),
    path('get/', views.get, name='get'),
    path('infoscan/', views.infoscan, name='infoscan'),
    path('infoscan/status', views.infoscan_status, name='infoscan_status'),
]
