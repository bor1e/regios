from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/network/
    path('add', views.add, name='add_network'),
    path('<network_name>', views.network, name='network'),
    path('change_domain_relation/<network_name>',
         views.change_domain_relation),
    path('add_domain/<network_name>', views.add_domain_to_network,
         name='add_domain'),
    path('update/<network_name>', views.update_network,
         name='update_network'),
]
