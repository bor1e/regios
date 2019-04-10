from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/
    path('', views.index, name='start'),
    path('edit/<domain>/info/<external>', views.edit_info, name='edit_info'),
]
