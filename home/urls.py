from django.urls import path
from . import views

urlpatterns = [
	# 127.0.0.1:8000/
    path('', views.index, name='index'),
    path('api/crawl/', views.crawl, name='api'),
    path('domain=<domain>', views.domain, name='domain'),
    path('start_external_crawling=<domain>', views.external_crawling, name='crawling'),
    path('filter=<src_domain>/<external_domain>', views.filter, name='filter'),
]