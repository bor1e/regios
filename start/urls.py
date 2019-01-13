from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/api/
    path('', views.index, name='start'),
    path('edit/<domain>/zip/<external>', views.edit_zip, name='edit_zip'),
    path('edit/<domain>/name/<external>', views.edit_name, name='edit_name'),
]
