from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/network/
    path('add', views.add, name='add_network'),
    path('<network_name>', views.network, name='network'),
    path('add_domain/<network_name>', views.add_domain_to_network,
         name='add_domain'),

]
