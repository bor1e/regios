from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/graph/
    # path('', views.index, name='complete_graph'),
    path('', views.index, name='show_full_graph'),
    path('<domain>', views.index, name='show_graph'),
    path('init/', views.init_graph, name='init_full_graph'),
    path('init/<domain>', views.init_graph, name='init_graph'),
    # path('api/', views.api, name='api'),
    path('test/', views.test, name='test-sigmajs'),
]
