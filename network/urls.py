from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/network/
    path('add', views.add, name='add_network'),
    path('<network_name>', views.network, name='network'),
]
