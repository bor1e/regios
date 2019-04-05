from django.urls import path
from . import views

urlpatterns = [
    # 127.0.0.1:8000/display/
    path('check', views.check, name='check'),
    path('<domain>', views.display, name='display'),
    path('progress/<domain>', views.progress, name='progress'),
    path('<domain>/refresh', views.refresh, name='refresh'),
    path('<domain>/selected', views.externals_selected,
         name='externals_selected'),
]
