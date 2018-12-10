from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/filter/
    path('<src_domain>/<external_domain>',
         views.add_to_blacklist, name='filter'),
]
