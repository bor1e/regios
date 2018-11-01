from django.urls import path
from . import views

urlpatterns = [
	# 127.0.0.1:8000/
    path('', views.index, name='home'),
    path('post/', views.post, name='post'),
    path('thanks', views.index, name='thanks'),
]