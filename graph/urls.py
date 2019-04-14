from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/graph/
    # path('', views.index, name='complete_graph'),
    path('', views.index, name='show_full_graph'),
    path('<domain>', views.index, name='show_graph'),
    path('init/', views.init_graph, name='init_full_graph'),
    path('init/<domain>', views.init_graph, name='init_graph'),


    path('network/<network_name>', views.network_index, name='graph_network'),
    path('network/init/<network_name>', views.network_init,
         name='graph_init_network'),

    path('test/', views.test, name='test-sigmajs'),
]
