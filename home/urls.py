from django.urls import path
from . import views

urlpatterns = [
	# 127.0.0.1:8000/
    path('', views.index, name='home'),
    #path('post', views.post, name='post'),
    #url(r'^api/crawl/', views.crawl, name='crawl'),
    #! TODO: check for ^ , $  and r in beginning of string
    path('api/crawl/', views.crawl, name='crawl'),
    path('domain/', views.domain, name='domain'),
]