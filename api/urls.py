from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
	# 127.0.0.1:8000/api/
	# displays process for single site
    #path('one', views.one, name='one'), 
    # displays process for all not filtered links
    path('multiple', views.multiple, name='multiple'),
    # start spider, get status information
    path('post/', views.post, name='post'),
    path('get/', views.get, name='get'),

]