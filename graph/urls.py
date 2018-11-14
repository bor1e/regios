from django.urls import path
from . import views

urlpatterns = [
	# 127.0.0.1:8000/
    path('', views.index, name='graph'),
    path('api/', views.api, name='api'),
]