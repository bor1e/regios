from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/actor/
    path('index', views.index, name='index'),
    path('create', views.create, name='create_actor'),
    # path('add', views.add, name='add_actor'),
]
