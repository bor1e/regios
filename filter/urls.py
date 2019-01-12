from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/filter/
    path('', views.display_filter, name='display_full_filter'),
    path('<src_domain>', views.display_filter, name='display_filter'),
    path('remove/<ignore>', views.remove_filter, name='remove_filter'),
    path('manual/',
         views.manual_add_to_blacklist, name='manual_filter'),
    path('<src_domain>/<external_domain>',
         views.add_to_blacklist, name='filter'),
    path('<domain>/<local_ignore>',
         views.add_to_localfilter, name='add_to_localfilter'),
    path('remove/<local_ignore>',
         views.remove_from_localfilter, name='remove_from_localfilter')
]
