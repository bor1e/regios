from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    # 127.0.0.1:8000/api/
    path('post/', views.post, name='post'),
    path('get/', views.get, name='get'),
    path('check-infoscan/', views.check_infoscan, name='check_infoscan'),
    path('infoscan/', views.infoscan, name='infoscan'),
    path('scrapy_jobs_status/', views.scrapy_jobs_status,
         name='scrapy_jobs_status'),
    # path('selected/', views.selected, name='selected'),
    path('cancel_job/<job_id>', views.cancel_job, name='cancel_job'),
]
